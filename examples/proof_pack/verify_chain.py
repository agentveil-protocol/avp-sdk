"""
Standalone AVP audit-chain verifier.

Reference implementation of the audit hash-chain verification logic.
Does NOT depend on the agentveil SDK — stdlib only.

    python verify_chain.py artifacts/08_audit_trail.json
    python verify_chain.py artifacts/08_audit_trail.json --verbose

Hash formula (matches the AVP backend implementation):

    entry_hash = SHA256(
        previous_hash_or_empty
        + event_type
        + agent_did
        + canonical_json(payload)
        + iso8601_timestamp
    )

where canonical_json uses sort_keys=True, separators=(",",":").

Chain validity requires BOTH:
  - every entry's entry_hash recomputes correctly from its fields
  - every entry's previous_hash equals the preceding entry's entry_hash

Entries must be ordered by ascending sequence_number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any


def _normalize_ts(ts: str) -> str:
    """
    Normalize the API's ISO timestamp back to Python datetime.isoformat() form.

    Backend hashes with datetime.isoformat() which produces '+00:00' suffix for
    UTC. FastAPI/Pydantic serializes the same datetime as trailing 'Z' in JSON.
    Recomputing the hash requires reversing that substitution.
    """
    if ts.endswith("Z"):
        return ts[:-1] + "+00:00"
    return ts


def recompute_hash(entry: dict[str, Any]) -> str:
    prev = entry.get("previous_hash") or ""
    payload = entry.get("payload")
    payload_json = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) if payload else ""
    )
    message = (
        prev
        + entry["event_type"]
        + entry["agent_did"]
        + payload_json
        + _normalize_ts(entry["created_at"])
    )
    return hashlib.sha256(message.encode()).hexdigest()


def verify_chain(entries: list[dict[str, Any]], *, check_linkage: bool = False) -> dict[str, Any]:
    """
    Verify audit entries offline.

    check_linkage=True : require adjacent entries to link via previous_hash.
                         Only correct on a FULL dump of the chain.
    check_linkage=False: only recompute each entry's entry_hash (subset-safe).
                         Use this on per-DID trails returned by /v1/audit/{did},
                         which intentionally skip unrelated events but still
                         carry a correct previous_hash pointing at the globally
                         preceding entry.

    Every entry's stored previous_hash is still covered because it contributes
    to the hashed message. Tampering with any field (including previous_hash)
    breaks the per-entry recompute.
    """
    if not entries:
        return {"valid": True, "checked": 0, "errors": []}

    entries = sorted(entries, key=lambda e: e["sequence_number"])
    errors: list[dict[str, Any]] = []

    for i, entry in enumerate(entries):
        if check_linkage:
            expected_prev = entries[i - 1]["entry_hash"] if i > 0 else None
            if entry.get("previous_hash") != expected_prev:
                errors.append(
                    {
                        "sequence": entry["sequence_number"],
                        "error": "chain_break",
                        "detail": f"previous_hash={entry.get('previous_hash')!r} expected={expected_prev!r}",
                    }
                )
        recomputed = recompute_hash(entry)
        if recomputed != entry["entry_hash"]:
            errors.append(
                {
                    "sequence": entry["sequence_number"],
                    "error": "hash_mismatch",
                    "detail": f"recomputed={recomputed} stored={entry['entry_hash']}",
                }
            )

    mode = "full_chain_linkage_and_hash" if check_linkage else "subset_hash_recompute"
    scope = (
        "Verifies every entry's hash recomputes AND adjacent previous_hash "
        "linkage. Only meaningful when the input is the full global audit "
        "chain, not a per-DID trail."
        if check_linkage
        else "Verifies every entry's stored entry_hash recomputes correctly "
             "from its fields. Safe on per-DID trails (GET /v1/audit/{did}) "
             "which are intentionally a SUBSET of the global chain. This "
             "proves per-entry tamper resistance, NOT global chain completeness. "
             "For global chain integrity, query the server's GET /v1/audit/verify."
    )
    return {
        "valid": not errors,
        "checked": len(entries),
        "verification_mode": mode,
        "scope": scope,
        "first_sequence": entries[0]["sequence_number"],
        "last_sequence": entries[-1]["sequence_number"],
        "last_hash": entries[-1]["entry_hash"],
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify AVP audit-chain integrity offline.")
    ap.add_argument("path", help="Path to JSON file containing an array of audit entries.")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument(
        "--full-chain",
        action="store_true",
        help="Treat the input as the full audit chain and also verify adjacent "
             "previous_hash linkage. Default: per-entry integrity only "
             "(safe on per-DID trails that intentionally skip entries).",
    )
    ap.add_argument(
        "--out",
        help="Optional path to write the verification result JSON (e.g. artifacts/09_chain_verification.json).",
    )
    args = ap.parse_args()

    with open(args.path) as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("ERROR: input must be a JSON array of audit entries", file=sys.stderr)
        return 2

    result = verify_chain(data, check_linkage=args.full_chain)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)

    if args.verbose or not result["valid"]:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"chain valid: {result['checked']} entries, "
            f"sequences {result['first_sequence']}..{result['last_sequence']}"
        )

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
