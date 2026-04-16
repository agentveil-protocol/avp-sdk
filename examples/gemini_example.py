"""
Google Gemini + Agent Veil Protocol integration example.

Shows how to:
    1. Register agents on AVP
    2. Define AVP trust tools as Gemini function declarations
    3. Gemini calls trust tools via function calling
    4. Log interaction results as attestations

Prerequisites:
    pip install agentveil google-generativeai

Usage:
    python examples/gemini_example.py
"""

import json

from agentveil import AVPAgent

AVP_URL = "https://agentveil.dev"


# === AVP tool handlers ===

_avp_agent = None


def _get_agent() -> AVPAgent:
    global _avp_agent
    if _avp_agent is None:
        _avp_agent = AVPAgent.load(AVP_URL, "gemini_researcher")
    return _avp_agent


def check_reputation(did: str) -> dict:
    """Check an agent's reputation score on AVP."""
    return _get_agent().get_reputation(did)


def trust_check(did: str, min_tier: str = "basic") -> dict:
    """Advisory trust decision: should I delegate to this agent?"""
    return _get_agent().can_trust(did, min_tier=min_tier)


def log_attestation(did: str, outcome: str, context: str = "") -> dict:
    """Log an interaction result as a signed attestation."""
    return _get_agent().attest(to_did=did, outcome=outcome, context=context)


TOOL_HANDLERS = {
    "check_reputation": check_reputation,
    "trust_check": trust_check,
    "log_attestation": log_attestation,
}


def main():
    # === Step 1: Register agents ===
    print("=== Registering agents on AVP ===")

    researcher = AVPAgent.create(AVP_URL, name="gemini_researcher")
    researcher.register(
        display_name="Gemini Researcher",
        capabilities=["research", "analysis"],
        provider="google",
    )

    assistant = AVPAgent.create(AVP_URL, name="gemini_assistant")
    assistant.register(
        display_name="Gemini Assistant",
        capabilities=["writing", "summarization"],
        provider="google",
    )

    print(f"Researcher: {researcher.did[:40]}...")
    print(f"Assistant:  {assistant.did[:40]}...")

    # === Step 2: Simulate tool calls ===
    print("\n=== Simulating tool calls ===")

    rep = check_reputation(assistant.did)
    print(f"Reputation: score={rep['score']:.3f}, confidence={rep['confidence']:.3f}")

    decision = trust_check(assistant.did, min_tier="basic")
    print(f"Trust: allowed={decision['allowed']}, tier={decision['tier']}")

    att = log_attestation(assistant.did, "positive", "research_task")
    print(f"Attestation: {att}")

    # === Step 3: Updated reputation ===
    print("\n=== Updated reputation ===")
    rep = researcher.get_reputation(assistant.did)
    print(f"Assistant: score={rep['score']:.3f}, confidence={rep['confidence']:.3f}")

    # === Step 4: Gemini function calling (requires GOOGLE_API_KEY) ===
    print("\n=== Gemini function calling (requires GOOGLE_API_KEY) ===")
    print("""
    # To run with Gemini:
    #
    # import google.generativeai as genai
    #
    # genai.configure(api_key="YOUR_API_KEY")
    #
    # tools = genai.protos.Tool(function_declarations=[
    #     genai.protos.FunctionDeclaration(
    #         name="check_reputation",
    #         description="Check an agent's reputation score on AVP",
    #         parameters=genai.protos.Schema(
    #             type=genai.protos.Type.OBJECT,
    #             properties={"did": genai.protos.Schema(type=genai.protos.Type.STRING)},
    #             required=["did"],
    #         ),
    #     ),
    #     genai.protos.FunctionDeclaration(
    #         name="trust_check",
    #         description="Advisory trust decision: should I delegate to this agent?",
    #         parameters=genai.protos.Schema(
    #             type=genai.protos.Type.OBJECT,
    #             properties={
    #                 "did": genai.protos.Schema(type=genai.protos.Type.STRING),
    #                 "min_tier": genai.protos.Schema(type=genai.protos.Type.STRING),
    #             },
    #             required=["did"],
    #         ),
    #     ),
    #     genai.protos.FunctionDeclaration(
    #         name="log_attestation",
    #         description="Log a signed attestation after interaction",
    #         parameters=genai.protos.Schema(
    #             type=genai.protos.Type.OBJECT,
    #             properties={
    #                 "did": genai.protos.Schema(type=genai.protos.Type.STRING),
    #                 "outcome": genai.protos.Schema(type=genai.protos.Type.STRING),
    #                 "context": genai.protos.Schema(type=genai.protos.Type.STRING),
    #             },
    #             required=["did", "outcome"],
    #         ),
    #     ),
    # ])
    #
    # model = genai.GenerativeModel("gemini-1.5-pro", tools=[tools])
    # chat = model.start_chat()
    #
    # response = chat.send_message("Check if %s is trustworthy")
    #
    # # Handle function calls
    # for part in response.parts:
    #     if fn := part.function_call:
    #         args = dict(fn.args)
    #         result = TOOL_HANDLERS[fn.name](**args)
    #         response = chat.send_message(
    #             genai.protos.Content(parts=[
    #                 genai.protos.Part(function_response=genai.protos.FunctionResponse(
    #                     name=fn.name, response={"result": result}
    #                 ))
    #             ])
    #         )
    #         print(response.text)
    """ % assistant.did)

    print("=== Done ===")


if __name__ == "__main__":
    main()
