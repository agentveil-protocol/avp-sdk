#!/usr/bin/env python3
"""
Terminal demo for GIF recording — shows the AVP control-layer narrative in 5 scenes.

Uses only the public SDK in mock mode. No backend, no webhook URLs,
no internal thresholds, no admin surfaces.

Record with asciinema:
    asciinema rec docs/demo.cast -c "python examples/demo_gif.py"
Convert to GIF:
    agg docs/demo.cast docs/demo.gif --cols 72 --rows 28 --speed 1
"""

import hashlib
import time

from agentveil import AVPAgent

# ANSI colors
G = "\033[32m"   # green
R = "\033[31m"   # red
Y = "\033[33m"   # yellow
B = "\033[34m"   # blue
C = "\033[36m"   # cyan
W = "\033[1;37m" # bold white
D = "\033[2m"    # dim
RST = "\033[0m"  # reset


def p(text, delay=0.5):
    """Print a line and pause. Base cadence 0.5s (was 0.6s in v1)."""
    print(text, flush=True)
    time.sleep(delay)


def header(num, title):
    print(flush=True)
    p(f"{W}{'=' * 60}{RST}", 0.15)
    p(f"{W}  [{num}/5] {title}{RST}", 0.15)
    p(f"{W}{'=' * 60}{RST}", 0.5)


# ── Intro ──
print(flush=True)
p(f"{C}  Agent Veil Protocol{RST}", 0.35)
p(f"{D}  decide before action, monitor trust, alert on change,{RST}", 0.2)
p(f"{D}  leave verifiable proof{RST}", 0.9)

# ── Scene 1: Trust check — before action ──
header("1", "Trust check \u2014 before action")

p(f"{D}>>> from agentveil import AVPAgent{RST}", 0.3)
p(f"{D}>>> alice = AVPAgent.create(mock=True, name='alice'){RST}", 0.3)
alice = AVPAgent.create(mock=True, name="alice")
p(f"{D}>>> bob   = AVPAgent.create(mock=True, name='bob'){RST}", 0.3)
bob = AVPAgent.create(mock=True, name="bob")
alice.register(display_name="alice")
bob.register(display_name="bob")
p(f"{G}  \u2713 two agents registered with DID identity{RST}", 0.6)

p(f"{D}>>> alice.can_trust(bob.did, min_tier='basic'){RST}", 0.4)
p(f"{G}  {{{RST}", 0.15)
p(f'{G}    "allowed": true,{RST}', 0.2)
p(f'{G}    "tier": "basic",{RST}', 0.2)
p(f'{G}    "risk_level": "low",{RST}', 0.2)
p(f'{G}    "reason": "agent meets basic requirement"{RST}', 0.2)
p(f"{G}  }}{RST}", 0.9)

# ── Scene 2: Action — delegation ──
header("2", "Action \u2014 delegation")

p(f"{D}>>> alice publishes a job, bob accepts and completes it{RST}", 0.4)
p(f"{G}  \u2713 job: code review   \u2192 published{RST}", 0.3)
p(f"{G}  \u2713 job accepted       \u2192 by bob{RST}", 0.3)
p(f"{G}  \u2713 job completed      \u2192 result delivered{RST}", 0.9)

# ── Scene 3: Signal changes — trust degrades ──
header("3", "Signal changes \u2014 trust degrades")

p(f"{D}>>> a counter-party submits a signed negative attestation{RST}", 0.4)
p(f"{D}    with context + evidence hash{RST}", 0.3)
ev = hashlib.sha256(b"demo:evidence").hexdigest()
alice.attest(
    bob.did,
    outcome="negative",
    weight=1.0,
    context="code_review",
    evidence_hash=ev,
)
p(f"{Y}  \u26a1 reputation recomputes on the next cycle{RST}", 0.5)
p(f"{Y}  \u26a1 risk_level moved up, signal recorded{RST}", 0.9)

# ── Scene 4: Alert + deny — webhook fires ──
header("4", "Alert + deny \u2014 webhook fires")

p(f"{D}>>> alice.can_trust(bob.did, min_tier='basic')  # re-check{RST}", 0.4)
p(f"{R}  {{{RST}", 0.15)
p(f'{R}    "allowed": false,{RST}', 0.2)
p(f'{R}    "tier": "newcomer",{RST}', 0.2)
p(f'{R}    "risk_level": "medium",{RST}', 0.2)
p(f'{R}    "reason": "agent tier below required basic"{RST}', 0.2)
p(f"{R}  }}{RST}", 0.5)
print(flush=True)
p(f"{D}  webhook payload delivered to your endpoint:{RST}", 0.3)
p(f"{Y}  {{ \"event\": \"score_drop\", \"trigger\": \"score_below_threshold\",{RST}", 0.2)
p(f'{Y}    "payload_schema_version": 2 }}{RST}', 0.9)

# ── Scene 5: Proof — offline-verifiable audit ──
header("5", "Proof \u2014 offline-verifiable audit")

p(f"{D}>>> every decision is appended to a hash-chained audit trail{RST}", 0.4)
p(f"{D}>>> anyone can verify it without our server:{RST}", 0.4)
print(flush=True)
p(f"{D}  $ python verify_chain.py audit_trail.json{RST}", 0.4)
p(f"{G}  chain valid: 7 entries, per-entry integrity confirmed{RST}", 0.7)
print(flush=True)
p(f"{W}  decide \u2192 act \u2192 monitor \u2192 revoke \u2192 prove{RST}", 0.5)

# ── Outro ──
print(flush=True)
p(f"{W}{'=' * 60}{RST}", 0.15)
p(f"{G}  https://agentveil.dev{RST}", 0.3)
p(f"{G}  pip install agentveil{RST}", 0.3)
p(f"{W}{'=' * 60}{RST}", 0.5)
print(flush=True)
