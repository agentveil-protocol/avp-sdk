"""
Standalone AVP Reputation Credential Verification

Verify an AVP reputation credential WITHOUT the agentveil SDK.
Only requires: PyNaCl (Ed25519) and base58.

    pip install pynacl base58

This script demonstrates that any system can verify AVP credentials
offline — just check the Ed25519 signature and TTL.
"""

import json
from datetime import datetime, timezone

import base58
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def verify_avp_credential(credential: dict) -> dict:
    """
    Verify an AVP reputation credential.

    Returns a dict with:
        valid: bool — True if signature is correct and not expired
        reason: str — human-readable status
    """
    # 1. Check all required fields exist
    required = (
        "did", "score", "confidence", "issued_at",
        "expires_at", "risk_level", "signature", "signer_did",
    )
    for field in required:
        if field not in credential:
            return {"valid": False, "reason": f"Missing field: {field}"}

    # 2. Check TTL — credential must not be expired
    try:
        expires_at = datetime.strptime(
            credential["expires_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return {"valid": False, "reason": "Invalid expires_at format"}

    if datetime.now(timezone.utc) > expires_at:
        return {"valid": False, "reason": "Credential expired"}

    # 3. Extract Ed25519 public key from signer_did (did:key:z...)
    signer_did = credential["signer_did"]
    if not signer_did.startswith("did:key:z"):
        return {"valid": False, "reason": "Invalid signer_did format"}

    try:
        decoded = base58.b58decode(signer_did[9:])  # strip "did:key:z"
    except Exception:
        return {"valid": False, "reason": "Failed to decode signer_did"}

    # Multicodec: 0xED 0x01 = Ed25519 public key
    if len(decoded) < 34 or decoded[0] != 0xED or decoded[1] != 0x01:
        return {"valid": False, "reason": "Invalid Ed25519 multicodec prefix"}

    public_key = decoded[2:]

    # 4. Reconstruct the signed payload (everything except signature and signer_did)
    payload = {
        k: v for k, v in credential.items()
        if k not in ("signature", "signer_did")
    }
    # Canonical JSON: sorted keys, no whitespace
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    # 5. Verify Ed25519 signature
    try:
        signature = bytes.fromhex(credential["signature"])
    except ValueError:
        return {"valid": False, "reason": "Invalid signature hex"}

    try:
        verify_key = VerifyKey(public_key)
        verify_key.verify(message, signature)
    except BadSignatureError:
        return {"valid": False, "reason": "Signature verification failed"}
    except Exception as e:
        return {"valid": False, "reason": f"Verification error: {e}"}

    return {"valid": True, "reason": "Credential is valid and not expired"}


# --- Example usage ---
if __name__ == "__main__":
    import sys

    # You can pass a credential JSON file as argument, or use the inline example
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            cred = json.load(f)
    else:
        # Fetch a live credential from AVP
        try:
            import httpx
            target_did = "did:key:z6Mk..."  # replace with a real DID
            base_url = "https://agentveil.dev"
            r = httpx.get(
                f"{base_url}/v1/reputation/{target_did}/credential",
                params={"risk_level": "low"},
            )
            r.raise_for_status()
            cred = r.json()
            print("Fetched credential from AVP:")
            print(json.dumps(cred, indent=2))
            print()
        except Exception as e:
            print(f"Could not fetch live credential: {e}")
            print("Pass a credential JSON file as argument:")
            print(f"  python {sys.argv[0]} credential.json")
            sys.exit(1)

    result = verify_avp_credential(cred)
    print(f"Verification result: {result['reason']}")
    print(f"Valid: {result['valid']}")
