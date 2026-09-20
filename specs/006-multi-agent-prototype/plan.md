# Implementation Plan: Multi-Agent Research Assistant Prototype

**Branch**: `006-multi-agent-prototype` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-multi-agent-prototype/spec.md` — Build a Multi-Agent System Prototype for an academic research assistant (PDF: `src/advanced-multi-agent-ai-system-course/module_3/Build a MultiAgent System Prototype.pdf`).

## Summary

Build a working LangGraph prototype that processes an academic research query through **4 specialized agents** — Literature Search, Analysis, Synthesis, and optional Citation Verification — demonstrating task decomposition, structured inter-agent communication with context preservation, and governance (credibility checks, conflict resolution, observability). The system runs end-to-end on mock literature data in under 5 minutes and produces four submission artifacts: documented source code, architecture diagram, sample output, and brief reflection.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: `langgraph ^1.2.6`, `langchain ^1.3.10`, `langchain-openai ^1.3.2`, `pydantic ^2.0`, `pydantic-settings ^2.0`, `loguru ^0.7.3`, `grandalf ^0.8` (diagram layout), `pymupdf ^1.27` (optional PDF export for sample output) — all already in the approved stack (Constitution VI). No new dependencies.

**Storage**: In-memory `StateGraph` state. Optional `MemorySaver`/`InMemorySaver` checkpointer for streaming/debugging extension. No external DB.

**Testing**: `unittest` (stdlib) mirrored under `tests/research_assistant_prototype/`. Shared helpers in `tests/base.py`. Each `TestCase` covers one class/function; integration tests cover inter-agent communication and schema contracts.

**Target Platform**: Linux server (project standard). Runs locally via `poetry run python`.

**Project Type**: Library module (`src/research_assistant_prototype/`). New top-level package alongside `langgraph_course` — keeps the advanced-course prototype isolated while remaining importable via the existing Poetry package configuration (addition to `pyproject.toml:packages`).

**Performance Goals**: Mock-data end-to-end workflow completes within 5 minutes (SC-001). Per-agent latency observable via `@timed_node`. Budget enforcement within 30s of overrun.

**Constraints**: 3 mandatory agents + 1 optional (4 total, satisfies FR-001/FR-010). Source credibility signal on every source (FR-011). Conflict detection/resolution on every run (FR-012). Telemetry on every activation (FR-013). `ruff check` must pass (SC-009).

**Scale/Scope**: Single-user prototype evaluation. Not multi-tenant. Mock external services (FR-020). Sample query: "What are the latest advances in transformer efficiency for low-resource languages?" (consistent across docs/tests).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Rule | Compliance | Notes |
|---------|------|------------|-------|
| I — LangGraph Patterns | StateGraph, pydantic/TypedDict state, Node/Edge/ConditionalEdge, Annotated[list, add_messages] | ✅ PASS | Sequential pipeline + conditional edges (validate, budget, synthesis trigger) maps directly to StateGraph primitives. State defined via `pydantic.BaseModel`. |
| II — Config-Driven Design | Settings class, .env, no hardcoded values | ✅ PASS | `Settings` from `src/config.py` + `.env`; `LLMFactory` for provider/model selection. No hardcoded API keys or model names. |
| III — Observability | @timed_node per node, loguru, list[ErrorRecord], exponential backoff, processing_outcome="partial" | ✅ PASS | `@timed_node` on each agent node; `loguru` for structured logs; `ErrorRecord` TypedDict in state; retry with backoff; degraded synthesis tagged partial. |
| IV — LLM Abstraction | LLMFactory only; @register_provider for extensions | ✅ PASS | All LLM calls via `utils/llm.py:LLMFactory.create()`. No direct ChatOpenAI instantiation in nodes. |
| V — Test Discipline | unittest, mirrored structure, 1 class per subject, integration tests for contracts | ✅ PASS | Tests under `tests/research_assistant_prototype/` mirroring source; contract + integration tests included. |
| VI — Dependency Discipline | No new deps without justification; prefer approved stack | ✅ PASS | Uses only approved dependencies (langgraph, langchain, pydantic, loguru, grandalf, pymupdf). No new packages added. |

**Verdict**: ALL GATES PASS. No complexity tracking required.

## Research

See [research.md](research.md) for 7 design decisions covering framework selection, agent specialization, coordination topology, mock literature strategy, credibility/conflict mechanisms, observability/error handling, and diagram/sample output production.

## Project Structure

### Documentation (this feature)

```text
specs/006-multi-agent-prototype/
├── plan.md              # This file
├── research.md          # Phase 0 — 7 design decisions
├── data-model.md        # Phase 1 — 9 entities with validation & state transitions
├── quickstart.md        # Phase 1 — 6 validation scenarios
├── contracts/
│   ├── agent-interfaces.md   # Per-agent + coordination contracts
│   └── api-contracts.md      # Public entry points (run_research, stream, CLI)
└── tasks.md             # Phase 2 (/speckit.tasks) — not created here
```

### Source Code (repository root)

```text
src/
├── config.py
├── research_assistant_prototype/          # NEW package for this prototype
│   ├── __init__.py
│   ├── state.py                          # ResearchRequest, SourceRecord, Finding, Conflict, SharedState, SynthesisReport, TelemetryEvent, ErrorRecord
│   ├── graph.py                          # ResearchAssistantGraph + create_full_graph() + run_research()/stream_research()
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── literature_search.py          # LiteratureSearchAgent (mock retrieval + credibility scoring)
│   │   ├── analysis.py                   # AnalysisAgent (insight extraction with provenance)
│   │   ├── citation_verification.py     # CitationVerificationAgent (optional, FR-010)
│   │   └── synthesis.py                  # SynthesisAgent (cross-referenced summary + conflict disclosures)
│   ├── coordination/
│   │   ├── __init__.py
│   │   ├── router.py                     # validate_query, check_execution_budget, should_synthesize
│   │   └── conflict.py                   # detect_conflicts + resolve_conflicts
│   ├── telemetry/
│   │   ├── __init__.py
│   │   └── events.py                     # TelemetryEvent builders + timed_node integration
│   └── artifacts/
│       ├── __init__.py
│       ├── diagram.py                    # Generates architecture diagram (grandalf/mermaid)
│       └── sample_output.py              # Runs sample query and writes sample_output.md
├── langgraph_course/                     # existing
└── utils/                                # LLMFactory, decorators, etc.

tests/
└── research_assistant_prototype/
    ├── __init__.py
    ├── test_state.py                     # Entity validation & state transitions
    ├── test_literature_search.py         # Literature search + credibility
    ├── test_analysis.py                  # Analysis node in isolation
    ├── test_citation_verification.py    # Citation verification (optional agent)
    ├── test_synthesis.py                 # Synthesis with cross-references
    ├── test_conflict.py                  # Conflict detection + resolution
    ├── test_router.py                    # Validation, budget, synthesis triggers
    ├── test_telemetry.py                 # Telemetry + ErrorRecord
    └── test_integration.py              # End-to-end paths (happy, degraded, conflict, empty)

# Docs produced by the prototype (committed as submission artifacts)
docs/
└── 006-prototype/
    ├── architecture_diagram.png (or .svg)
    ├── sample_output.md
    └── reflection.md
```

**Structure Decision**: Single new library package `src/research_assistant_prototype/` rather than nesting under `src/langgraph_course/module_3/labs/` or the hyphenated `src/advanced-multi-agent-ai-system-course/` path (which is not a valid Python package and is not listed in `pyproject.toml`). Adding `{include="research_assistant_prototype", from="src"}` to `pyproject.toml:packages` makes the prototype importable (`from research_assistant_prototype.graph import run_research`) while keeping the PDF's conceptual placement documented in the reflection and diagram. Tests mirror the source under `tests/research_assistant_prototype/`. The topology is a sequential pipeline with conditional edges for validation and budget enforcement — the simplest topology that satisfies FR-003/FR-004 while remaining inspectable and LangSmith-compatible.

## Complexity Tracking

Not required — Constitution Check passed with no violations.
