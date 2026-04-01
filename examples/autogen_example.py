"""
AutoGen + Agent Veil Protocol — E2E example.

An AutoGen AssistantAgent that uses AVP reputation tools to verify
another agent before delegating work.

Prerequisites:
    pip install agentveil autogen-agentchat "autogen-ext[openai]"
    export OPENAI_API_KEY="sk-..."

Usage:
    python examples/autogen_example.py
"""

import asyncio
import os
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agentveil import AVPAgent
from agentveil.tools.autogen import (
    check_avp_reputation,
    should_delegate_to_agent,
    log_avp_interaction,
    configure,
)

AVP_URL = "https://agentveil.dev"


async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    # === Step 1: Configure AVP and register agents ===
    configure(base_url=AVP_URL, agent_name="autogen_researcher")

    print("=== Registering agents on AVP ===")

    researcher = AVPAgent.create(AVP_URL, name="autogen_researcher")
    researcher.register(display_name="AutoGen Researcher")
    researcher.publish_card(capabilities=["research", "analysis"], provider="openai")

    writer = AVPAgent.create(AVP_URL, name="autogen_writer")
    writer.register(display_name="AutoGen Writer")
    writer.publish_card(capabilities=["writing", "editing"], provider="openai")

    print(f"  Researcher DID: {researcher.did[:40]}...")
    print(f"  Writer DID:     {writer.did[:40]}...")

    # === Step 2: Create AutoGen agent with AVP tools ===
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    agent = AssistantAgent(
        name="reputation_checker",
        model_client=model_client,
        tools=[check_avp_reputation, should_delegate_to_agent, log_avp_interaction],
        system_message=(
            "You are a reputation-aware AI agent. You use Agent Veil Protocol "
            "tools to verify other agents before collaborating. Always check "
            "reputation first, then make a delegation decision, and log the "
            "interaction result."
        ),
        reflect_on_tool_use=True,
    )

    # === Step 3: Run the agent ===
    print("\n=== Running AutoGen agent ===\n")

    task = (
        f"I need to delegate a research task to the agent with DID '{writer.did}'. "
        "First check their reputation, then decide whether to delegate with a "
        "minimum score of 0.3. If approved, log a positive interaction. "
        "Give me a summary of what you found."
    )

    await Console(agent.run_stream(task=task))

    # === Step 4: Verify reputation changed ===
    print("\n=== Updated reputation ===")
    rep = researcher.get_reputation(writer.did)
    print(f"  Writer: score={rep['score']:.3f}, confidence={rep['confidence']:.3f}")

    await model_client.close()
    print("\n=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
