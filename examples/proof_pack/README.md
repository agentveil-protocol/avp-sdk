# AVP Proof Pack — internal demo (Step 2)

> Status: **internal only**. Do not publish, do not push to public `avp-sdk`.
> Derived public/buyer cuts come in Step 2.5 / Step 3.

One runnable walkthrough of the full AVP trust lifecycle:

> **AVP decides whether an agent should act, monitors trust during execution, revokes it on degradation, fires an alert, and leaves a cryptographic audit trail anyone can verify offline.**

---

## What this demo proves

| Scene | Artifact | What it shows |
|---|---|---|
| 1 | `01_registration.json` | Two real DIDs, PoW + verify path |
| 2 | `02_initial_trust_check.json` | `can_trust` returns `allowed=true` initially |
| 3 | `03_job_delegation.json` | Real Jobs API cycle: publish → accept → complete |
| 4 | `04_negative_attestation.json` | Real `POST /v1/attestations` with `outcome=negative` |
| 5 | `05_score_drop.json` | Real EigenTrust recompute run via job runner; score before/after |
| 6 | `06_trust_check_denied.json` | Same `can_trust` call now returns different tier / deny |
| 7 | `07_webhook_alert.json` | Real dispatcher payload delivered via HTTP to local receiver |
| 8 | `08_audit_trail.json` | Full audit chain for the worker agent |
| 9 | `09_chain_verification.json` | **Client-side subset integrity** — recomputes every entry hash in the per-DID trail. Proves per-entry tamper resistance. |
| 9b | `09b_server_full_chain_reference.json` | **Server-side full-chain reference** — result of `GET /v1/audit/verify` walking the entire global chain. Included as a reference check, trusts the server. |

Only the webhook **transport** is local (HTTP to `localhost:8765`). Payload,
trigger conditions, and dispatcher path are production code.

---

## Prerequisites

1. **Local AVP backend** (from the private `avp/` repo) running via `docker compose`:
   ```bash
   cd /path/to/avp
   # Ensure .env has ENVIRONMENT=development so /v1/alerts accepts http:// URLs
   docker compose up -d
   curl http://localhost:8000/v1/health   # should return ok
   ```
2. **Python deps** in this directory:
   ```bash
   pip install agentveil httpx pynacl base58
   ```

---

## Run

Terminal A (webhook sink, must be up first):
```bash
cd avp-sdk/examples/proof_pack
python webhook_receiver.py            # listens on http://127.0.0.1:8765/hook
```

Terminal B (orchestrator):
```bash
cd avp-sdk/examples/proof_pack
python run_demo.py \
    --server http://localhost:8000 \
    --compose-service api \
    --compose-dir /path/to/avp \
    --webhook-url http://host.docker.internal:8765/hook \
    --threshold 0.99
```

Expected runtime: **under 5 minutes**. End state: `artifacts/` has 9 JSON files
and the orchestrator prints `PROOF PACK DEMO COMPLETE`.

### Common parameters

| Flag | Default | Purpose |
|---|---|---|
| `--server` | `http://localhost:8000` | Local AVP backend |
| `--compose-service` | `api` | Service name in `docker-compose.yml` (NOT container name) |
| `--compose-dir` | cwd | Directory containing `docker-compose.yml` |
| `--webhook-url` | `http://host.docker.internal:8765/hook` | URL the AVP container posts to. On Linux, use `http://172.17.0.1:8765/hook` or wire a bridge network alias. |
| `--threshold` | `0.99` | Alert fires below this score. High threshold ensures the first negative attestation trips it. |

---

## Offline chain verification (standalone)

**Subset trail verification ≠ global chain integrity verification.**

`verify_chain.py` has **zero AVP dependencies** (stdlib only — hashlib, json):

```bash
# Subset mode (default): per-entry hash recompute. Safe on /v1/audit/{did}.
python verify_chain.py artifacts/08_audit_trail.json --verbose

# Full-chain mode: additionally checks adjacent previous_hash linkage.
# Only correct on a full global chain dump, NOT on a per-DID trail.
python verify_chain.py full_chain_dump.json --full-chain --verbose
```

**What this verifier proves (subset mode):** every entry in the trail has a
stored `entry_hash` that correctly recomputes from its fields. Any tampering
with any field (including `previous_hash`) breaks the recompute. This proves
per-entry tamper resistance without trusting the server.

**What it does NOT prove:** that the global audit chain has no missing or
inserted entries outside the returned subset. `GET /v1/audit/{did}` is
intentionally a subset — the backend trail endpoint skips unrelated events.
For global completeness, use the server-side `GET /v1/audit/verify` reference
(saved as `09b_server_full_chain_reference.json`).

Reference hash formula, documented at `avp/app/core/audit/chain.py:42-47`:

```
entry_hash = SHA256(
    previous_hash_or_empty
    + event_type
    + agent_did
    + canonical_json(payload)     # sort_keys=True, separators=(",",":")
    + iso8601_timestamp            # backend uses "+00:00"; API responses
                                   # emit "Z" — verifier normalizes back.
)
```

Any system — auditor, regulator, customer — can run this file against an AVP
audit trail JSON and independently verify per-entry integrity.

---

## Reuse vs. copy (Step 2 rule)

Per `PROOF_PACK_PLAN.md` §Step 2 ground rules:

- `verify_chain.py` — **copied logic** from `app/core/audit/chain.py`.
  It is a reference re-implementation, intentionally duplicated so it can run
  without the AVP backend.
- `run_demo.py` — **imports** `AVPAgent` from the public `agentveil` SDK; does
  NOT import from sibling examples (`jobs_demo.py` has module-level side
  effects and a prod URL). The `jobs_request` helper is copied locally (10 lines).

No changes outside `proof_pack/` were made in Step 2.

---

## Known gotchas

- **`host.docker.internal`** works on Docker Desktop (macOS/Windows) out of the
  box. On Linux, add `extra_hosts: ["host.docker.internal:host-gateway"]` to
  the `api` service or use the host bridge IP.
- **`ENVIRONMENT=development`** is required in `.env` — production config
  rejects non-HTTPS webhook URLs (`app/api/v1/alerts.py:42` → `validate_url`).
- **Recompute timing**: the dispatcher fires synchronously during the compute
  job. If no alert lands in `07_webhook_alert.json`, check the job stdout
  (saved in `05_score_drop.json.recompute.stdout_tail`).
- **Threshold 0.99** is intentionally high. Real deployments use ~0.5. With 0.99
  any initial negative attestation crosses it. Do not carry this value forward
  to any buyer-facing or public cut.
- **Fresh DIDs per run.** Agents are not saved to disk (`save=False`). Run
  cleanup: `docker compose down -v` between runs if you want a clean slate.

---

## Definition of done (Step 2)

All must hold on a clean run against local docker-compose:

- [x] 9 JSON artifacts generated under `artifacts/`
- [x] Artifact 05 shows before/after with non-equal scores
- [x] Artifact 07 contains a real dispatcher payload delivered via HTTP
- [x] Artifact 09 reports `valid: true`, `checked > 0`
- [x] `verify_chain.py` imports only stdlib (no `agentveil`)
- [x] Zero files changed outside `proof_pack/`
- [x] Zero pushes to public `avp-sdk`

Mutation test (tamper with hash → expect `invalid`) is **not** a DoD gate —
left as optional follow-up per Step 2 ground rules.

---

## Next steps (not Step 2)

- **Step 2.5** — derive a private buyer cut: remove recompute mechanics, admin
  surfaces, internal thresholds; keep the runnable flow.
- **Step 3** — derive a public sanitized cut: annotated walkthrough + reference
  verifier + 5 curated artifacts + architecture boundary diagram. Push to
  `avp-sdk` **only** after Codex review.
