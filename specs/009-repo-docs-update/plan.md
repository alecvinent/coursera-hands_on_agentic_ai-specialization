# Implementation Plan: Course README & General README Update

**Branch**: `009-repo-docs-update` | **Date**: 2026-09-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-repo-docs-update/spec.md`

## Summary

Create 7 per-course README.md files under each course directory in `src/` and restructure the root README.md from a monolithic LangGraph-focused document into a navigation hub that links to per-course READMEs. Move all detailed LangGraph pattern documentation (9-pattern table, architecture diagrams, decision framework, enterprise considerations) into the LangGraph course README. Preserve the LinkedIn summary, shared setup instructions, and `AGENTS.md` reference in the root README.

## Technical Context

**Language/Version**: Markdown (documentation only — no code changes)

**Primary Dependencies**: None

**Storage**: N/A (markdown files tracked by git)

**Testing**: Manual verification — confirm all 7 READMEs exist, root README links work, content is preserved

**Target Platform**: GitHub repository web UI

**Project Type**: Documentation

**Performance Goals**: N/A

**Constraints**: Must preserve existing content (LinkedIn summary, shared setup, AGENTS.md reference). Must not break external links. MCP course READMEs must link to existing task-level READMEs, not duplicate them.

**Scale/Scope**: 7 new files + 1 modified file. ~8 markdown files total.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution.md found. No governance gates to evaluate. Proceeding.

## Project Structure

### Documentation (this feature)

```text
specs/009-repo-docs-update/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (not applicable — no external interfaces)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── langgraph_course/
│   └── README.md                    # NEW — Course 1 README (absorbs root pattern docs)
├── multiagent-governance_course/
│   └── README.md                    # NEW — Course 2 README
├── building-ai-agents-for-complex-tasks/
│   └── README.md                    # NEW — Course 3 README
├── advanced-multi-agent-ai-system-course/
│   └── README.md                    # NEW — Course 4 README
├── mcp-model-content-protocol-course/
│   └── README.md                    # NEW — Course 5 README (links to task1/task2 READMEs)
├── agentic-ai-protocols-mcp-a2a-acp-course/
│   └── README.md                    # NEW — Course 6 README
└── ethical-governance--risk-in-agentic-ai-course/
    └── README.md                    # NEW — Course 7 README

README.md                            # MODIFIED — Restructured as navigation hub
```

**Structure Decision**: Documentation-only feature. 7 new markdown files in existing directories + 1 modified root file. No new directories, no code changes, no configuration changes.

## Complexity Tracking

No constitution violations — this is a documentation task with no architectural complexity.
