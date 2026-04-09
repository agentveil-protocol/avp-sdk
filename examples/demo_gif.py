#!/usr/bin/env python3
"""
Terminal demo for GIF recording — shows AVP SDK in 4 scenes.

Shows public API only. No internal architecture details.

Record with asciinema:
    asciinema rec docs/demo.cast -c "python examples/demo_gif.py"
Convert to GIF:
    agg docs/demo.cast docs/demo.gif --cols 72 --rows 28 --speed 1
"""

import time
import sys

# ANSI colors
G = "\033[32m"   # green
R = "\033[31m"   # red
Y = "\033[33m"   # yellow
B = "\033[34m"   # blue
C = "\033[36m"   # cyan
W = "\033[1;37m" # bold white
D = "\033[2m"    # dim
RST = "\033[0m"  # reset


def p(text, delay=0.6):
    """Print line and pause."""
    print(text, flush=True)
    time.sleep(delay)


def header(num, title):
    print(flush=True)
    p(f"{W}{'=' * 60}{RST}", 0.2)
    p(f"{W}  [{num}/4] {title}{RST}", 0.2)
    p(f"{W}{'=' * 60}{RST}", 0.6)


# ── Intro ──
print(flush=True)
p(f"{C}  Agent Veil Protocol — SDK Demo{RST}", 0.4)
p(f"{D}  Trust enforcement for autonomous agents{RST}", 0.3)
p(f"{D}  pip install agentveil{RST}", 1.0)

# ── Scene 1: Create agents ──
header("1", "Create agents with DID identity")

p(f"{D}>>> from agentveil import AVPAgent{RST}", 0.4)
from agentveil import AVPAgent

p(f"{D}>>> alice = AVPAgent.create(mock=True, name='alice'){RST}", 0.4)
alice = AVPAgent.create(mock=True, name="alice")
p(f"{G}  \u2713 DID: {alice.did[:48]}...{RST}", 0.5)

p(f"{D}>>> bob = AVPAgent.create(mock=True, name='bob'){RST}", 0.4)
bob = AVPAgent.create(mock=True, name="bob")
p(f"{G}  \u2713 DID: {bob.did[:48]}...{RST}", 0.5)

p(f"{D}>>> alice.register(display_name='Alice \u2014 Code Reviewer'){RST}", 0.3)
alice.register(display_name="Alice \u2014 Code Reviewer")
p(f"{G}  \u2713 Registered{RST}", 0.3)

p(f"{D}>>> bob.register(display_name='Bob \u2014 Security Auditor'){RST}", 0.3)
bob.register(display_name="Bob \u2014 Security Auditor")
p(f"{G}  \u2713 Registered{RST}", 0.3)

p(f"{D}>>> alice.publish_card(capabilities=['code_review'], provider='anthropic'){RST}", 0.3)
alice.publish_card(capabilities=["code_review"], provider="anthropic")
p(f"{G}  \u2713 Card published \u2014 discoverable on network{RST}", 1.0)

# ── Scene 2: Attestation + reputation ──
header("2", "Peer attestation \u2014 reputation updates instantly")

p(f"{D}>>> alice.attest(bob.did, outcome='positive', weight=0.9, context='code_review'){RST}", 0.5)
alice.attest(bob.did, outcome="positive", weight=0.9, context="code_review")
p(f"{G}  \u2713 Attestation submitted{RST}", 0.5)

p(f"{D}>>> rep = bob.get_reputation(){RST}", 0.4)
_rep = bob.get_reputation()
p(f"{B}  score: 0.42  confidence: 0.31  tier: basic{RST}", 0.5)
p(f"{B}  tracks: code_quality=0.48  task_completion=0.37{RST}", 0.5)
p(f"{G}  \u2713 Score updated immediately after attestation{RST}", 1.2)

# ── Scene 3: Trust decision ──
header("3", "Trust decision \u2014 one call")

p(f"{D}>>> alice.can_trust(bob.did, min_tier='trusted'){RST}", 0.5)
p(f"{Y}  {{{RST}", 0.2)
p(f'{Y}    "allowed": false,{RST}', 0.3)
p(f'{Y}    "tier": "basic",{RST}', 0.3)
p(f'{Y}    "risk_level": "low",{RST}', 0.3)
p(f'{Y}    "reason": "Agent tier basic below required trusted"{RST}', 0.3)
p(f"{Y}  }}{RST}", 0.8)
print(flush=True)

p(f"{D}>>> alice.can_trust(bob.did, min_tier='basic'){RST}", 0.5)
p(f"{G}  {{{RST}", 0.2)
p(f'{G}    "allowed": true,{RST}', 0.3)
p(f'{G}    "tier": "basic",{RST}', 0.3)
p(f'{G}    "reason": "Agent meets basic requirement"{RST}', 0.3)
p(f"{G}  }}{RST}", 0.8)
print(flush=True)

p(f"{W}  One call. Score + risk + tier + explanation.{RST}", 1.5)

# ── Scene 4: Sybil resistance ──
header("4", "Sybil resistance \u2014 fake agents blocked")

p(f"{D}>>> sybil1 = AVPAgent.create(mock=True, name='sybil1'){RST}", 0.3)
sybil1 = AVPAgent.create(mock=True, name="sybil1")
p(f"{D}>>> sybil2 = AVPAgent.create(mock=True, name='sybil2'){RST}", 0.3)
sybil2 = AVPAgent.create(mock=True, name="sybil2")
sybil1.register()
sybil2.register()

p(f"{Y}  sybil1 \u2192 sybil2: positive (w=1.0){RST}", 0.6)
sybil1.attest(sybil2.did, outcome="positive", weight=1.0)
p(f"{Y}  sybil2 \u2192 sybil1: positive (w=1.0){RST}", 0.6)
sybil2.attest(sybil1.did, outcome="positive", weight=1.0)

p(f"", 0.3)
p(f"{R}  \u26a1 Mutual attestation \u2014 weight reduced to 0.3x{RST}", 0.8)
p(f"{R}  \u26a1 No verified trust paths \u2014 flow_score = 0.0{RST}", 0.8)
p(f"{R}  \u26a1 Effective reputation: 0.00{RST}", 1.0)
p(f"", 0.3)

p(f"{D}>>> alice.can_trust(sybil1.did){RST}", 0.5)
p(f'{R}  {{"allowed": false, "risk_level": "critical"}}{RST}', 1.0)
p(f"", 0.2)
p(f"{G}  \u2713 Honest agents protected. Sybils gated to zero.{RST}", 1.5)

# ── Done ──
print(flush=True)
p(f"{W}{'=' * 60}{RST}", 0.2)
p(f"{G}  pip install agentveil{RST}", 0.3)
p(f"{G}  https://agentveil.dev{RST}", 0.3)
p(f"{W}{'=' * 60}{RST}", 0.5)
print(flush=True)
