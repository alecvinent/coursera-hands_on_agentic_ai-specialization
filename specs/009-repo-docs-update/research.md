# Research: Course README & General README Update

**Date**: 2026-09-20
**Feature**: 009-repo-docs-update

## Current State Analysis

### Root README (852 lines)

The current root README is focused almost entirely on the LangGraph Framework course:
- Lines 1-22: Title, LinkedIn summary, key skills, stack
- Lines 23-52: Module breakdown (Module 1-4) — LangGraph specific
- Lines 53-161: Overview, project structure, how to work on exercises, Flowise guide, prerequisites, setup, API keys, calling providers
- Lines 162-288: Running tests, Streamlit UI
- Lines 289-852: Multi-Agent System Patterns — the 9-pattern table, architecture diagrams, decision framework, enterprise considerations (~560 lines of LangGraph-specific content)

**Preserved in root README after update**: Title, LinkedIn summary, shared prerequisites/setup/API keys, high-level directory tree, links to all 7 course READMEs, condensed LangGraph summary.

**Moved to LangGraph course README**: 9-pattern table, all 9 pattern architecture sections, choosing-a-pattern decision framework, enterprise considerations, resources.

### Course Inventory

| # | Directory | Modules | Has Code | Has README | Topic |
|---|-----------|---------|----------|------------|-------|
| 1 | `langgraph_course/` | 3 + agents/ | YES (most developed) | NO | LangGraph workflows, state mgmt, multi-agent research |
| 2 | `multiagent-governance_course/` | 3 | YES (Python packages) | NO | Agent classification, content pipelines, governance |
| 3 | `building-ai-agents-for-complex-tasks/` | 3 | YES (agent.py files) | NO | Agent types, multi-step agents, behavior diagnosis |
| 4 | `advanced-multi-agent-ai-system-course/` | 3 | YES (agent.py in mod3) | NO | Multi-agent architecture, governance, prototype |
| 5 | `mcp-model-content-protocol-course/` | 3 | YES (full MCP server) | YES (2 at task level) | MCP evaluation, schemas, production MCP server |
| 6 | `agentic-ai-protocols-mcp-a2a-acp-course/` | 3 | NO (text only) | NO | MCP/A2A/ACP protocol analysis and design |
| 7 | `ethical-governance--risk-in-agentic-ai-course/` | 3 | NO (text only) | NO | Ethics, autonomy, compliance, governance |

### Shared Infrastructure

All courses share:
- `src/config.py` — pydantic-settings configuration
- `src/models.py` — Shared LangGraph State TypedDict
- `src/log.py` — loguru configuration
- `src/utils/` — LLMFactory, provider registry, @timed_node decorator, AgentBase ABC

### Test Coverage by Course

| Course | Test Directory | Test Count |
|--------|---------------|------------|
| langgraph_course | `tests/test_module_1/`, `tests/test_module_2/`, `tests/test_module_3/`, `tests/test_agents/` | ~150+ tests |
| multiagent-governance_course | `tests/multiagent-governance_course/` | ~50+ tests |
| building-ai-agents-for-complex-tasks | None | 0 |
| advanced-multi-agent-ai-system-course | None | 0 |
| mcp-model-content-protocol-course | `src/.../module_3/task1/tests/` (colocated) | 62 tests |
| agentic-ai-protocols-mcp-a2a-acp-course | None | 0 |
| ethical-governance--risk-in-agentic-ai-course | None | 0 |

### Existing Sub-Project READMEs (FR-007 — must link, not duplicate)

- `src/mcp-model-content-protocol-course/module_3/task1/README.md` — Secure MCP Server (93 lines): API reference, setup, run, test, deploy
- `src/mcp-model-content-protocol-course/module_3/task2/README.md` — MCP Enterprise Portfolio (60 lines): capstone setup and deployment
- `docs/flowise-course-end-project/README.md` — Flowise course-end project guide (254 lines)

## Per-Course Content Decisions

### Course 1: LangGraph Framework

**Absorbs root pattern documentation** (FR-006). This README will be the longest (~300-400 lines) since it contains:
- Course overview and module listing
- The 9-pattern table (from root README lines 298-316)
- All 9 pattern architecture sections with diagrams (lines 368-734)
- Choosing-a-pattern decision framework (lines 736-794)
- Enterprise considerations (lines 796-838)
- Resources (lines 839-843)
- Module-specific lab instructions

**Run commands**: `poetry run python -m src.langgraph_course.module_3.labs.patterns.coordinator` etc.
**Test commands**: `poetry run python -m unittest tests.test_module_1 -v` etc.

### Course 2: Multi-Agent Design & Governance

**Modules**:
- Module 1: Agent classification, interaction maps, trade-off analysis
- Module 2: Sequential Researcher -> Writer -> SEO blog pipeline
- Module 3: Course-end governance project (PDFs only)

**Run commands**: `poetry run python -m src.multiagent-governance_course.module_2_multiagents` (CLI entry)
**Test commands**: `python -m unittest discover -s tests/multiagent-governance_course -t . -v`

### Course 3: Building AI Agents for Complex Tasks

**Modules**:
- Module 1: Agent type classification (text exercises, classifications.txt)
- Module 2: Multi-step agent building (2 tasks with agent.py)
- Module 3: Behavior diagnosis and real-world agent (3 tasks with agent.py)

**Run commands**: `python agent.py` from task directories
**Test commands**: None (no test suite)

### Course 4: Advanced Multi-Agent AI Systems

**Modules**:
- Module 1: Multi-agent system architecture design (text exercise)
- Module 2: Governance framework implementation (text exercise)
- Module 3: Multi-agent prototype + design portfolio (2 agent.py implementations)

**Run commands**: `python agent.py` from task3/task1/ and task3/task2/
**Test commands**: None

### Course 5: MCP (Model Context Protocol)

**Modules**:
- Module 1: MCP evaluation for AI integration scenarios
- Module 2: MCP resource schema design
- Module 3: Complete MCP server with security/monitoring + enterprise portfolio

**Existing READMEs**: Link to `module_3/task1/README.md` and `module_3/task2/README.md`
**Run commands**: Docker-based (`docker compose up`), Poetry for local dev
**Test commands**: `poetry run python -m pytest` (62 tests in task1)

### Course 6: Agentic AI Protocols (MCP/A2A/ACP)

**Modules**:
- Module 1: MCP architecture analysis
- Module 2: A2A task coordination design
- Module 3: Multi-protocol implementation plans

**No code** — all text-based exercises with PDFs and question files
**Run commands**: N/A (read-only exercises)
**Test commands**: N/A

### Course 7: Ethical Governance & Risk in Agentic AI

**Modules**:
- Module 1: AI autonomy level assessment
- Module 2: Multi-jurisdictional AI compliance strategy
- Module 3: Healthcare AI governance framework + domain-specific exercises

**No code** — all text-based exercises with framework documents
**Run commands**: N/A
**Test commands**: N/A

## Root README Structure (Post-Update)

```markdown
# Coursera Agentic AI Specialization

[One-paragraph description]

## LinkedIn Summary
[Preserved as-is]

## Courses
[Table: Course | Topic | Link to README]

## Shared Setup
[Prerequisites, Poetry install, API keys — condensed from current root]

## Project Structure
[High-level directory tree]

## AGENTS.md Reference
[Kept as-is]

## Flowise Course-end Project
[Link to docs/flowise-course-end-project/README.md]

## Resources
[Condensed from current root]
```
