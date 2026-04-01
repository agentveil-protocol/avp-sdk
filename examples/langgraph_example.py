"""
LangGraph + Agent Veil Protocol — E2E example.

A tool-calling agent that uses AVP reputation tools inside a LangGraph
StateGraph to verify another agent before delegating work.

Prerequisites:
    pip install agentveil langgraph langchain-openai langchain-core
    export OPENAI_API_KEY="sk-..."

Usage:
    python examples/langgraph_example.py
"""

import os
import sys

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from agentveil import AVPAgent
from agentveil.tools.langgraph import (
    avp_check_reputation,
    avp_should_delegate,
    avp_log_interaction,
    configure,
)

AVP_URL = "https://agentveil.dev"


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: Set OPENAI_API_KEY environment variable.")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    # === Step 1: Configure AVP and register agents ===
    configure(base_url=AVP_URL, agent_name="langgraph_researcher")

    print("=== Registering agents on AVP ===")

    researcher = AVPAgent.create(AVP_URL, name="langgraph_researcher")
    researcher.register(display_name="LangGraph Researcher")
    researcher.publish_card(capabilities=["research", "analysis"], provider="openai")

    writer = AVPAgent.create(AVP_URL, name="langgraph_writer")
    writer.register(display_name="LangGraph Writer")
    writer.publish_card(capabilities=["writing", "editing"], provider="openai")

    print(f"  Researcher DID: {researcher.did[:40]}...")
    print(f"  Writer DID:     {writer.did[:40]}...")

    # === Step 2: Build LangGraph with AVP tools ===
    tools = [avp_check_reputation, avp_should_delegate, avp_log_interaction]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: MessagesState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    app = graph.compile()

    # === Step 3: Run the agent ===
    print("\n=== Running LangGraph agent ===\n")

    query = (
        f"I need to delegate a research task to the agent with DID '{writer.did}'. "
        "First check their reputation using check_avp_reputation, then decide "
        "whether to delegate using should_delegate with a minimum score of 0.3. "
        "If approved, log a positive interaction using log_avp_interaction. "
        "Give me a summary of what you found."
    )

    result = app.invoke({"messages": [("user", query)]})

    # Print the final response
    print("=== Agent response ===")
    print(result["messages"][-1].content)

    # === Step 4: Verify reputation changed ===
    print("\n=== Updated reputation ===")
    rep = researcher.get_reputation(writer.did)
    print(f"  Writer: score={rep['score']:.3f}, confidence={rep['confidence']:.3f}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
