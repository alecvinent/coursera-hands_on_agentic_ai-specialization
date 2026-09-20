# Coursera Agentic AI Specialization

Hands-on workbook for the [Coursera Agentic AI Specialization](https://www.coursera.org/specializations). Implements production-grade multi-agent systems, MCP servers, governance frameworks, and protocol designs across 7 courses.

> AI coding assistants working on this repo should read [`AGENTS.md`](AGENTS.md) for conventions, testing setup, and agent behavior guidelines.

## LinkedIn Summary

**LangGraph Framework — Multi-Agent Systems & Stateful LLM Workflows**

Built production-grade multi-agent AI systems using LangGraph, LangChain, and LangSmith. Implemented 9 multi-agent coordination patterns (coordinator, specialist, event-driven, ReAct, reflection, planning, tool, sequential, human-in-the-loop) across 11 standalone graph implementations with unified support-ticket domain, `@timed_node` observability, and `interrupt()`/`MemorySaver` checkpointing.

**Key skills demonstrated**:

- **Agentic AI Architecture** — Designed typed state schemas, conditional routing, and cyclic graphs for dynamic multi-agent orchestration
- **State Management** — Implemented persistent shared state across 5-agent workflows with provenance chaining, conflict detection, circuit breakers, and graceful degradation
- **Observability** — Wired `@timed_node` telemetry, structured loguru logging, and `TelemetryEvent` records into every node; built real-time Streamlit streaming UI
- **Resilience Patterns** — Exponential backoff retry, input refinement gates, execution budget enforcement, and 3-strike circuit breakers routed via LangGraph conditional edges
- **Enterprise Patterns** — Checkpointing, interrupt/resume approval gates, per-thread workflow isolation, and modular pluggable agent nodes
- **Testing & Quality** — 35+ unittest test cases across state validation, node isolation, conflict resolution, routing logic, and end-to-end integration (3+ workflow paths)
- **Production Readiness** — `ruff` linting, Black formatting, pydantic-settings config, and `LLMFactory` provider abstraction (OpenRouter, OpenAI, Anthropic)

**Stack**: Python 3.10+ · LangGraph · LangChain · LangSmith · pydantic · loguru · Streamlit · Poetry

## Courses

| Course | Topic | Code? |
|--------|-------|-------|
| **[LangGraph Framework](src/langgraph_course/README.md)** | LangGraph workflows, state management, 9 multi-agent coordination patterns, tool-calling agents | Yes |
| **[Multi-Agent Design & Governance](src/multiagent-governance_course/README.md)** | Agent classification, sequential content pipelines, governance frameworks | Yes |
| **[Building AI Agents for Complex Tasks](src/building-ai-agents-for-complex-tasks/README.md)** | Agent type classification, multi-step agents, behavior diagnosis | Yes |
| **[Advanced Multi-Agent AI Systems](src/advanced-multi-agent-ai-system-course/README.md)** | Multi-agent architecture design, governance implementation, system prototypes | Yes |
| **[MCP (Model Context Protocol)](src/mcp-model-content-protocol-course/README.md)** | MCP evaluation, resource schemas, production MCP servers with security and monitoring | Yes |
| **[Agentic AI Protocols](src/agentic-ai-protocols-mcp-a2a-acp-course/README.md)** | MCP, A2A, and ACP protocol analysis and design | Text only |
| **[Ethical Governance & Risk](src/ethical-governance--risk-in-agentic-ai-course/README.md)** | AI autonomy assessment, compliance strategies, governance frameworks | Text only |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
poetry install
cp .env.example .env
```

Then edit `.env` with your API key(s). Available providers:

| Provider   | `llm_provider` | Required env vars                           |
|------------|----------------|---------------------------------------------|
| OpenRouter | `"openrouter"` | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` |
| OpenAI     | `"openai"`     | `LLM_API_KEY`                               |
| Anthropic  | `"anthropic"`  | `LLM_API_KEY`                               |

See individual course READMEs for course-specific setup instructions.

## Project Structure

```text
src/
├── langgraph_course/              # LangGraph Framework (3 modules + agents)
├── multiagent-governance_course/  # Multi-Agent Design & Governance (3 modules)
├── building-ai-agents-for-complex-tasks/  # Building AI Agents (3 modules)
├── advanced-multi-agent-ai-system-course/ # Advanced Multi-Agent Systems (3 modules)
├── mcp-model-content-protocol-course/     # MCP Course (3 modules)
├── agentic-ai-protocols-mcp-a2a-acp-course/  # Agentic AI Protocols (3 modules)
├── ethical-governance--risk-in-agentic-ai-course/ # Ethical Governance (3 modules)
├── config.py                # Shared configuration (API keys, model settings)
├── models.py                # Shared TypedDicts / Pydantic models
├── log.py                   # Loguru configuration
└── utils/                   # Shared utilities (LLMFactory, providers, decorators)
tests/                       # Unit tests mirroring source structure
docs/                        # Additional documentation
specs/                       # Feature specifications
```

## Flowise Course-end Project

The course-end project ("Designing an Autonomous E-commerce Support Crew") is a step-by-step guide for building a multi-agent system on a local Flowise instance. See:

- **[Guide](docs/flowise-course-end-project/README.md)** — build the three specialist agents, the orchestrator, and grading deliverables
- **[Feature spec](specs/005-flowise-guide/spec.md)** — requirements, user stories, and success criteria

## Resources

- [LangChain OpenTutorial — LangGraph Chatbot](https://langchain-opentutorial.gitbook.io/langchain-opentutorial/17-langgraph/01-core-features/02-langgraph-chatbot)
- [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/)
- [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/)
