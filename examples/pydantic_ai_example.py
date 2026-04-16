"""
PydanticAI + Agent Veil Protocol integration example.

Shows how to:
    1. Register an agent on AVP
    2. Define AVP trust tools as PydanticAI tools
    3. Agent checks reputation before acting
    4. Log interaction results as attestations

Prerequisites:
    pip install agentveil pydantic-ai

Usage:
    python examples/pydantic_ai_example.py
"""

from agentveil import AVPAgent

AVP_URL = "https://agentveil.dev"


def main():
    # === Step 1: Register agents on AVP ===
    print("=== Registering agents on AVP ===")

    analyst = AVPAgent.create(AVP_URL, name="pydantic_analyst")
    analyst.register(
        display_name="PydanticAI Analyst",
        capabilities=["analysis", "research"],
        provider="openai",
    )

    data_agent = AVPAgent.create(AVP_URL, name="pydantic_data")
    data_agent.register(
        display_name="PydanticAI Data Agent",
        capabilities=["data_processing"],
        provider="openai",
    )

    print(f"Analyst:    {analyst.did[:40]}...")
    print(f"Data Agent: {data_agent.did[:40]}...")

    # === Step 2: Trust check before delegation ===
    print("\n=== Trust check ===")
    decision = analyst.can_trust(data_agent.did, min_tier="basic")
    print(f"Can trust: {decision['allowed']} (tier: {decision['tier']}, score: {decision['score']:.3f})")
    print(f"Reason: {decision['reason']}")

    # === Step 3: Check reputation ===
    print("\n=== Reputation ===")
    rep = analyst.get_reputation(data_agent.did)
    print(f"Score: {rep['score']:.3f}, Confidence: {rep['confidence']:.3f}")

    # === Step 4: Log attestation ===
    print("\n=== Attestation ===")
    result = analyst.attest(
        to_did=data_agent.did,
        outcome="positive",
        weight=0.8,
        context="analysis_task",
    )
    print(f"Attestation logged: {result}")

    # === Step 5: PydanticAI agent with AVP tools (requires OPENAI_API_KEY) ===
    print("\n=== PydanticAI agent with AVP tools ===")
    print("""
    # To run with PydanticAI:
    #
    # from pydantic_ai import Agent, RunContext, Tool
    #
    # avp = AVPAgent.load("https://agentveil.dev", "pydantic_analyst")
    #
    # async def check_reputation(ctx: RunContext, did: str) -> dict:
    #     \"\"\"Check an agent's reputation score on AVP.\"\"\"
    #     return avp.get_reputation(did)
    #
    # async def trust_check(ctx: RunContext, did: str, min_tier: str = "basic") -> dict:
    #     \"\"\"Advisory trust decision: should I delegate to this agent?\"\"\"
    #     return avp.can_trust(did, min_tier=min_tier)
    #
    # async def log_attestation(ctx: RunContext, did: str, outcome: str, context: str = "") -> dict:
    #     \"\"\"Log an interaction result as a signed attestation.\"\"\"
    #     return avp.attest(to_did=did, outcome=outcome, context=context)
    #
    # agent = Agent(
    #     "openai:gpt-4",
    #     tools=[
    #         Tool(check_reputation, description="Check agent reputation on AVP"),
    #         Tool(trust_check, description="Check if agent meets trust threshold"),
    #         Tool(log_attestation, description="Log signed attestation after interaction"),
    #     ],
    #     system_prompt="You are an analyst. Check trust before delegating. Log results.",
    # )
    #
    # result = await agent.run("Check if %s is trustworthy for data processing")
    # print(result.data)
    """ % data_agent.did)

    print("=== Done ===")


if __name__ == "__main__":
    main()
