import os
import logging
from typing import TypedDict, Dict, Any

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# 1. LOGGING & DEBUG CONFIGURATION
# ---------------------------------------------------------------------------
# Requirement: Debug print or logging step to trace transitions
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("MultiStepAgent")


# ---------------------------------------------------------------------------
# 2. DEFINING AGENT STATE
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """
    Tracks the internal data passed between agent nodes across steps.
    """
    topic: str
    retrieved_data: str
    analysis: str
    final_summary: str
    error: bool


# ---------------------------------------------------------------------------
# 3. EXTERNAL TOOL & FALLBACK MECHANISM
# ---------------------------------------------------------------------------
# Requirement: External tool/function with error handling & retry/fallback logic
@tool
def mock_data_retriever_tool(query: str) -> str:
    """
    Simulates fetching data from an external API or database.
    """
    # Simulate API call failure for testing fallback logic
    if "fail" in query.lower():
        raise RuntimeError("External Data Retrieval Service is offline.")
    
    return f"Retrieved Data for '{query}': High demand detected, positive sentiment across customer reviews."


def safe_tool_execution(query: str) -> str:
    """
    Fallback wrapper to handle failures gracefully without crashing[cite: 1].
    """
    try:
        logger.info(f"[Tool Execution] Querying external tool with: '{query}'")
        return mock_data_retriever_tool.invoke({"query": query})
    except Exception as e:
        # Requirement: Safe default message or fallback logic on failure[cite: 1]
        logger.error(f"[Fallback Triggered] External tool error: {e}")
        return "DEFAULT_FALLBACK_DATA: System temporarily unable to retrieve fresh external data."


# ---------------------------------------------------------------------------
# 4. MULTI-STEP AGENT NODES
# ---------------------------------------------------------------------------
# Step 1: Retrieve Data[cite: 1]
def retrieve_node(state: AgentState) -> Dict[str, Any]:
    logger.info("--- [STEP 1] Transitioning to RETRIEVE NODE ---")
    topic = state.get("topic", "")
    
    data = safe_tool_execution(topic)
    is_error = "DEFAULT_FALLBACK_DATA" in data
    
    return {"retrieved_data": data, "error": is_error}


# Step 2: Analyze Data[cite: 1]
def analyze_node(state: AgentState) -> Dict[str, Any]:
    logger.info("--- [STEP 2] Transitioning to ANALYZE NODE ---")
    retrieved_data = state.get("retrieved_data", "")
    
    # Initialize LLM (Ensure OPENAI_API_KEY environment variable is set)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    prompt = f"Analyze the following data and extract 2 key actionable insights:\n\n{retrieved_data}"
    response = llm.invoke([
        SystemMessage(content="You are an expert data analyst."),
        HumanMessage(content=prompt)
    ])
    
    return {"analysis": response.content}


# Step 3: Format & Output Summary[cite: 1]
def output_summary_node(state: AgentState) -> Dict[str, Any]:
    logger.info("--- [STEP 3] Transitioning to OUTPUT SUMMARY NODE ---")
    analysis = state.get("analysis", "")
    topic = state.get("topic", "")
    
    summary = (
        f"=== FINAL AGENT REPORT ===\n"
        f"Topic: {topic.upper()}\n"
        f"Status: {'Completed with Fallback' if state.get('error') else 'Successfully Processed'}\n\n"
        f"Key Analysis & Insights:\n{analysis}\n"
        f"=========================="
    )
    
    return {"final_summary": summary}


# ---------------------------------------------------------------------------
# 5. GRAPH CONSTRUCTION & TRANSITIONS
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)

# Add processing nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("output", output_summary_node)

# Connect edges to define sequential 3-step workflow[cite: 1]
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "analyze")
workflow.add_edge("analyze", "output")
workflow.add_edge("output", END)

# Compile the agent graph
agent = workflow.compile()


# ---------------------------------------------------------------------------
# 6. EXECUTION DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n=== RUN 1: Standard Successful Execution ===")
    initial_state_success = {"topic": "AI Agent Market Trends"}
    result_1 = agent.invoke(initial_state_success)
    print("\n" + result_1["final_summary"])

    print("\n" + "="*50 + "\n")

    print("=== RUN 2: Simulating Tool Failure & Fallback Execution ===")
    initial_state_failure = {"topic": "Simulate failure condition"}
    result_2 = agent.invoke(initial_state_failure)
    print("\n" + result_2["final_summary"])