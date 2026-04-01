"""
CrewAI + Agent Veil Protocol — E2E example.

A research crew where agents check each other's reputation before
delegating work and log interaction results as attestations.

Prerequisites:
    pip install agentveil crewai
    export OPENAI_API_KEY="sk-..."

Usage:
    python examples/crewai_example.py
"""

import os
import sys

from crewai import Agent, Task, Crew, Process

from agentveil import AVPAgent
from agentveil.tools.crewai import (
    AVPReputationTool,
    AVPDelegationTool,
    AVPAttestationTool,
)

AVP_URL = "https://agentveil.dev"


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    # === Step 1: Register AVP identities ===
    print("=== Registering agents on AVP ===")

    researcher_avp = AVPAgent.create(AVP_URL, name="crewai_researcher")
    researcher_avp.register(display_name="CrewAI Researcher")
    researcher_avp.publish_card(capabilities=["research", "analysis"], provider="openai")

    writer_avp = AVPAgent.create(AVP_URL, name="crewai_writer")
    writer_avp.register(display_name="CrewAI Writer")
    writer_avp.publish_card(capabilities=["writing", "editing"], provider="openai")

    print(f"  Researcher DID: {researcher_avp.did[:40]}...")
    print(f"  Writer DID:     {writer_avp.did[:40]}...")

    # === Step 2: Create AVP tools ===
    avp_tools = [
        AVPReputationTool(base_url=AVP_URL, agent_name="crewai_researcher"),
        AVPDelegationTool(base_url=AVP_URL, agent_name="crewai_researcher"),
        AVPAttestationTool(base_url=AVP_URL, agent_name="crewai_researcher"),
    ]

    # === Step 3: Define CrewAI agents with AVP tools ===
    researcher = Agent(
        role="Research Analyst",
        goal=(
            "Find information about AI agent trust and verify collaborators "
            "using Agent Veil Protocol reputation tools"
        ),
        backstory=(
            "You are an expert researcher who always checks the reputation "
            "of other agents before collaborating. You have access to AVP tools "
            "to check reputation scores, make delegation decisions, and log "
            "interaction outcomes."
        ),
        tools=avp_tools,
        verbose=True,
    )

    writer = Agent(
        role="Technical Writer",
        goal="Write a clear summary based on research findings",
        backstory=(
            "You are a skilled technical writer who produces concise, "
            "well-structured reports."
        ),
        verbose=True,
    )

    # === Step 4: Define tasks ===
    research_task = Task(
        description=(
            f"Check the reputation of the agent with DID '{writer_avp.did}' "
            "using the check_avp_reputation tool. Then decide whether to delegate "
            "work to this agent using should_delegate_to_agent with a minimum "
            "score of 0.3. Report your findings about the agent's trustworthiness."
        ),
        expected_output=(
            "A short report containing: the agent's reputation score, "
            "confidence level, and your delegation decision with reasoning."
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            "Based on the research findings about AI agent trust verification, "
            "write a brief summary (3-5 sentences) explaining how Agent Veil "
            "Protocol helps agents verify each other's trustworthiness."
        ),
        expected_output="A concise paragraph about AVP trust verification.",
        agent=writer,
        context=[research_task],
    )

    # === Step 5: Run the crew ===
    print("\n=== Running CrewAI crew ===\n")

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n=== Crew result ===")
    print(result)

    # === Step 6: Log the interaction ===
    print("\n=== Logging interaction on AVP ===")
    att_tool = AVPAttestationTool(base_url=AVP_URL, agent_name="crewai_researcher")
    att_result = att_tool._run(
        did=writer_avp.did, outcome="positive", context="crewai_research_task"
    )
    print(f"Attestation recorded: {att_result}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
