# LangGraph Framework

Workbook for the [LangGraph Framework](https://www.coursera.org/learn/langgraph-framework) course on Coursera. Build stateful, multi-actor applications with Large Language Models using LangGraph, LangChain, and LangSmith.

## Modules

| Module | Topic | Key Files |
|--------|-------|-----------|
| 1 | LangGraph Architecture & Core Concepts | `labs/chatbot.py`, `labs/customer_inquiry.py`, `labs/tickets.py` |
| 2 | State Management & Resilience | `labs/legal_documents.py` |
| 3 | Multi-Agent Systems | `labs/patterns/` (11 patterns), `labs/multi_agent_research/` (5-agent system) |
| Agents | Tool-Calling Agents | `agents/cafe_agent.py`, `agents/weather_agent.py` |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- API key for an LLM provider (OpenRouter, OpenAI, or Anthropic)

## Setup

```bash
poetry install
cp .env.example .env
# Edit .env with your API key
```

## Running

```bash
# Module 1
poetry run python -m src.langgraph_course.module_1.labs.chatbot
poetry run python -m src.langgraph_course.module_1.labs.customer_inquiry
poetry run python -m src.langgraph_course.module_1.labs.tickets

# Module 2
poetry run python -m src.langgraph_course.module_2.labs.legal_documents

# Module 3 — Pattern implementations
poetry run python -m src.langgraph_course.module_3.labs.patterns.coordinator
poetry run python -m src.langgraph_course.module_3.labs.patterns.coordinator_cafe
poetry run python -m src.langgraph_course.module_3.labs.patterns.specialist
poetry run python -m src.langgraph_course.module_3.labs.patterns.event_driven_collaboration
poetry run python -m src.langgraph_course.module_3.labs.patterns.react
poetry run python -m src.langgraph_course.module_3.labs.patterns.reflection
poetry run python -m src.langgraph_course.module_3.labs.patterns.reflection_cafe
poetry run python -m src.langgraph_course.module_3.labs.patterns.planning
poetry run python -m src.langgraph_course.module_3.labs.patterns.tool
poetry run python -m src.langgraph_course.module_3.labs.patterns.sequential
poetry run python -m src.langgraph_course.module_3.labs.patterns.human_in_the_loop

# Agents
poetry run python -m src.langgraph_course.agents.cafe_agent
poetry run python -m src.langgraph_course.agents.weather_agent

# Streamlit UI
poetry run streamlit run streamlit_app.py
```

## Tests

```bash
# All tests
poetry run python -m unittest discover -v

# Module-specific
poetry run python -m unittest tests.test_module_1 -v
poetry run python -m unittest tests.test_module_2 -v
poetry run python -m unittest tests.test_module_3.test_coordinator -v
poetry run python -m unittest tests.test_module_3.test_coordinator_cafe -v
poetry run python -m unittest tests.test_agents.test_cafe_agent -v
```

## Multi-Agent System Patterns

Module 3 explores nine multi-agent coordination strategies, each implemented as a standalone LangGraph graph with the same support-ticket domain and consistent infrastructure (`@timed_node`, `interrupt()`/`Command()`, `MemorySaver`).

> Based on [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/).
> See also: [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/)

| Pattern | Communication | Routing Authority | Cross-Agent Flow |
|---------|---------------|-------------------|------------------|
| **Coordinator** | Hub-and-spoke | Central `coordinator` re-classifies every round | Coordinator reads agent response keywords |
| **Specialist** | Fully-connected mesh | Each specialist decides `route_to` | Specialist reads original `query` |
| **Event-Driven** | Pub-sub event queue | Event bus dispatches by event type subscription | Agent publishes events of different types |
| **ReAct** | Single-agent loop | Agent decides tool-to-call or respond | Agent calls tools → reads result → responds |
| **Reflection** | Generate → critique → refine | Critic evaluates and approves/revises | Generator produces draft, critic provides feedback |
| **Planning** | Plan → execute → review → repeat | Planner creates and tracks progress on ordered steps | Planner decomposes query, executor runs each step |
| **Tool** | Classify → run tool → format | Orchestrator selects single tool, formatter responds | Linear pipeline — one tool call, no loop |
| **Sequential** | Fixed-order linear pipeline | Each agent passes output to next in fixed sequence | Strict ordering — no routing, no loops |
| **Human-in-the-Loop** | Human-classify → agent → human-approve | Human decides topic and approves/rejects output | Human classifies, reviews, and provides revision feedback |

### Pattern Files

| File | Pattern | Domain | Agents / Tools |
|------|---------|--------|----------------|
| [`coordinator.py`](module_3/labs/patterns/coordinator.py) | Coordinator | Support tickets | agent\_a (billing), agent\_b (technical), agent\_c (general) |
| [`coordinator_cafe.py`](module_3/labs/patterns/coordinator_cafe.py) | Coordinator | Cafe | menu\_agent, order\_agent, customer\_agent |
| [`specialist.py`](module_3/labs/patterns/specialist.py) | Specialist | Support tickets | agent\_a, agent\_b, agent\_c |
| [`event_driven_collaboration.py`](module_3/labs/patterns/event_driven_collaboration.py) | Event-Driven | Support tickets | agent\_a, agent\_b, agent\_c |
| [`react.py`](module_3/labs/patterns/react.py) | ReAct | Support tickets | lookup\_invoice, check\_system\_status, escalate\_to\_human |
| [`reflection.py`](module_3/labs/patterns/reflection.py) | Reflection | Support tickets | generator, critic |
| [`reflection_cafe.py`](module_3/labs/patterns/reflection_cafe.py) | Reflection | Cafe | generator, critic |
| [`planning.py`](module_3/labs/patterns/planning.py) | Planning | Support tickets | planner, executor |
| [`tool.py`](module_3/labs/patterns/tool.py) | Tool | Support tickets | tool\_orchestrator, tool\_invoice, tool\_status, tool\_escalate, output\_formatter |
| [`sequential.py`](module_3/labs/patterns/sequential.py) | Sequential | Support tickets | analyzer, specialist, formatter |
| [`human_in_the_loop.py`](module_3/labs/patterns/human_in_the_loop.py) | Human-in-the-Loop | Support tickets | human\_classify, agent, human\_approve |

### Choosing a Pattern

Based on the article [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/):

1. **Is the workflow predictable?** If yes — sequential. If no — coordinator, specialist, or event-driven.
2. **Does quality matter more than speed?** If yes — reflection or human-in-the-loop. If no — ReAct, tool, sequential.
3. **Is the task genuinely complex?** If yes — planning or multi-agent. If no — single agent + tool use.

| Pattern | Cost | Latency | Reliability | Best For |
|---------|------|---------|-------------|----------|
| **ReAct** | Medium | Medium | Medium | Adaptive problem-solving with tool use |
| **Reflection** | High | High | High | Quality-critical content generation |
| **Planning** | Medium | Medium | High | Multi-step tasks with dependencies |
| **Tool** | Low | Low | Medium | Single-shot external data/integration |
| **Coordinator** | Medium | Medium | Medium | Hub-and-spoke domain routing |
| **Specialist** | Medium | Medium | Medium | Peer-to-peer task delegation |
| **Event-Driven** | Medium | Medium | High | Responsive cross-agent collaboration |
| **Sequential** | Low | Low | High | Fixed-order production pipelines |
| **Human-in-the-Loop** | Medium | High | High | High-stakes decisions requiring oversight |

### Evolution Path

```
Single Agent + Tool  ──►  Reflection  ──►  Multi-Agent  ──►  Human-in-the-Loop
       ↓                    ↓                  ↓                  ↓
     ReAct              Quality            Complexity           Safety
```

### Enterprise Considerations

Based on [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/):

- **Stateful Processing**: Checkpointing via `MemorySaver`, interrupt/resume via `interrupt()`/`Command()`, thread isolation per workflow run
- **Modular Agent Architecture**: Single responsibility per node, graph topology as architecture, pluggable nodes
- **Dynamic Workflow Management**: Static routing (Sequential, Tool), dynamic dispatch (Coordinator, Specialist, Event-Driven), adaptive loops (ReAct, Reflection, Planning)
- **Human-AI Collaboration**: Approval gates, redirect flows, revision feedback

| Concern | Implementation | Production Recommendation |
|---------|---------------|--------------------------|
| Checkpointing | `MemorySaver` (in-memory) | PostgreSQL or Redis `Checkpointer` |
| Observability | `@timed_node` decorator | LangSmith tracing |
| Error handling | `MAX_ROUNDS` safety valve | Exponential backoff, dead-letter queues |
| State persistence | Python `Dict` in-memory | Pydantic models with database serialization |
| Human handoff | `interrupt()` / `Command()` | Slack/email webhook notifications |

## Additional Resources

- [LangChain OpenTutorial — LangGraph Chatbot](https://langchain-opentutorial.gitbook.io/langchain-opentutorial/17-langgraph/01-core-features/02-langgraph-chatbot)
- [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/)
- [LangGraph: Architecting Advanced Multi-Agent Workflows](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/)
