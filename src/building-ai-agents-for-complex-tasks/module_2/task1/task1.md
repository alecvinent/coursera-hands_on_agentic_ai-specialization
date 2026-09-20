### **Pregunta 1: What part of the logic chain was hardest to implement?**

The most challenging part of the logic chain was **managing state resilience between the retrieval and analysis nodes when external tools fail**. Handling an unexpected runtime exception in a multi-step graph is straightforward, but preventing cascading downstream failures without breaking the graph's execution flow required iterating through specific architectural patterns.

Below is a detailed breakdown of the subproblems encountered, how they were iteratively implemented, and how the design choices were validated:

#### **1. Graceful Degradation vs. Hard Failure (Preventing LLM Hallucinations)**

* **The Challenge:** When an external tool fails, returning a standard generic error string (e.g., `"Error 500"`) often causes the downstream `analyze` node (LLM) to invent context, hallucinate facts, or try to analyze the literal text of the error message.


* **Implementation & Iteration:** I initially passed raw exception messages into the `AgentState`. When testing, the LLM attempted to analyze the word "Timeout" as if it were market data. To fix this, I implemented an explicit **Fallback Wrapper** around the tool execution:


```python
def safe_tool_execution(query: str) -> str:
    try:
        return mock_data_retriever_tool.invoke({"query": query})
    except Exception as e:
        logger.error(f"[Fallback Triggered] External tool error: {e}")
        return "DEFAULT_FALLBACK_DATA: System temporarily unable to retrieve fresh external data."

```


In addition, I updated the system prompt in the `analyze` node with explicit boundary conditions instructing the model to acknowledge data unavailability when `DEFAULT_FALLBACK_DATA` is detected rather than synthesizing insights.
* **Validation/Experiment:** I ran stress tests by passing query strings designed to trigger intentional exceptions (e.g., `"Simulate failure condition"`). I verified that the downstream analysis node gracefully output a structured warning instead of generating hallucinated metrics.



#### **2. State Propagation Across Nodes**

* **The Challenge:** Downstream nodes (like `output_summary`) need to know whether the upstream retrieval was clean or produced via a fallback mechanism, without having to re-inspect raw string outputs or re-execute tool logic.


* **Implementation & Iteration:** I implemented explicit state flags in the shared `AgentState` TypedDict:


```python
class AgentState(TypedDict):
    topic: str
    retrieved_data: str
    analysis: str
    final_summary: str
    error: bool  # Explicit status flag

```


During the `retrieve_node` step, the node evaluates the output of `safe_tool_execution` and explicitly sets `"error": True` in the dictionary update. This allowed subsequent nodes to read a boolean flag instantly.


* **Validation/Experiment:** I validated state integrity using assertions in test suites and real-time logging, confirming that `state["error"]` evaluated to `True` during failure conditions and `False` during standard executions.



#### **3. Control Flow & Routing Decisions**

* **The Challenge:** Determining whether a failed tool execution should immediately halt the pipeline, trigger retry logic, or proceed downstream with fallback context.


* **Implementation & Iteration:** In early iterations, tool exceptions caused hard crashes that terminated the entire execution thread. I refactored the design to decouple tool failure from graph execution, allowing the graph to always progress to completion while maintaining full visibility over state degradation.
