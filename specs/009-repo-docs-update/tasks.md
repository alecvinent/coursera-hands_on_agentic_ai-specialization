# Tasks: Course README & General README Update

**Input**: Design documents from `/specs/009-repo-docs-update/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not included — documentation-only feature, no test suite requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - Create Per-Course README Files (Priority: P1) 🎯 MVP

**Goal**: Each course directory under `src/` gets its own README.md explaining course content, modules, setup, and run instructions.

**Independent Test**: Verify all 7 course directories contain a README.md with course title, description, module listing, and setup/run/test instructions.

### Implementation for User Story 1

- [X] T001 [P] [US1] Create LangGraph Framework course README in src/langgraph_course/README.md — course title, description (3 modules + agents), module listing with topics, setup (Poetry + API keys), run commands for all 11 pattern implementations, test commands. This README absorbs the detailed pattern documentation (9-pattern table, architecture diagrams, decision framework, enterprise considerations) from the current root README.

- [X] T002 [P] [US1] Create Multi-Agent Design & Governance course README in src/multiagent-governance_course/README.md — course title, description (3 modules: agent classification, content pipeline, governance project), module listing, run commands (`poetry run python -m src.multiagent-governance_course.module_2_multiagents`), test commands (`python -m unittest discover -s tests/multiagent-governance_course -t . -v`).

- [X] T003 [P] [US1] Create Building AI Agents for Complex Tasks course README in src/building-ai-agents-for-complex-tasks/README.md — course title, description (3 modules: agent types, multi-step agents, behavior diagnosis), module listing with task counts, run commands (`python agent.py` from task directories), note no test suite.

- [X] T004 [P] [US1] Create Advanced Multi-Agent AI Systems course README in src/advanced-multi-agent-ai-system-course/README.md — course title, description (3 modules: architecture design, governance, prototype/portfolio), module listing, run commands (`python agent.py` from module_3 tasks), note no test suite.

- [X] T005 [P] [US1] Create MCP (Model Context Protocol) course README in src/mcp-model-content-protocol-course/README.md — course title, description (3 modules: MCP evaluation, schemas, production server), module listing, link to existing sub-project READMEs at module_3/task1/README.md and module_3/task2/README.md (FR-007 — do not duplicate), Docker and Poetry run commands, test commands (`poetry run python -m pytest`).

- [X] T006 [P] [US1] Create Agentic AI Protocols course README in src/agentic-ai-protocols-mcp-a2a-acp-course/README.md — course title, description (3 modules: MCP architecture, A2A coordination, multi-protocol plans), module listing, note this is a text/exercise-only course with no runnable code.

- [X] T007 [P] [US1] Create Ethical Governance & Risk course README in src/ethical-governance--risk-in-agentic-ai-course/README.md — course title, description (3 modules: autonomy assessment, compliance strategy, healthcare governance), module listing, note this is a text/exercise-only course with no runnable code.

**Checkpoint**: All 7 course READMEs exist and are self-contained. Each can be read independently to understand the course content.

---

## Phase 2: User Story 2 - Update General README as Hub (Priority: P2)

**Goal**: Restructure the root README.md from a monolithic LangGraph-focused document into a navigation hub linking to all 7 course READMEs.

**Independent Test**: Root README lists all courses with links, preserves LinkedIn summary, shared setup, and links to AGENTS.md. Pattern documentation content is no longer inline.

### Implementation for User Story 2

- [X] T008 [US2] Restructure root README.md — replace the current monolithic content with: title + one-paragraph specialization description, LinkedIn summary (preserved verbatim), courses table (7 rows with course name, topic, link to per-course README), shared setup section (prerequisites, Poetry install, API key configuration condensed from current root), high-level directory tree, AGENTS.md reference, Flowise guide link, resources. Target ~150-250 lines.

- [X] T009 [US2] Move all LangGraph pattern documentation from root README to src/langgraph_course/README.md — transfer the 9-pattern table (lines 298-316), all 9 pattern architecture sections with diagrams (lines 368-734), choosing-a-pattern decision framework (lines 736-794), enterprise considerations (lines 796-838), and resources (lines 839-843). Root README retains only a brief summary linking to the LangGraph course README for full details.

**Checkpoint**: Root README serves as a navigation hub. A new user can identify which course to start with and navigate to any course README in at most 2 clicks.

---

## Phase 3: User Story 3 - Consistent Documentation Quality (Priority: P3)

**Goal**: All README files follow a consistent structure with the same section headings, table format, and markdown conventions.

**Independent Test**: Compare section headings across all 7 per-course READMEs. Confirm they share the same structure (title, description, modules table, setup, running, tests).

### Implementation for User Story 3

- [X] T010 [US3] Audit and normalize all 7 per-course READMEs for consistent structure — verify each has: `# Course Title`, 1-3 sentence description, `## Modules` with table (Module | Topic | Key Files), `## Prerequisites` (if different from shared), `## Setup`, `## Running`, `## Tests` (or note "N/A"), `## Additional Resources`. Fix any inconsistencies in heading levels, table format, or code block style.

- [X] T011 [US3] Run quickstart.md validation scenarios — execute all 8 validation scenarios from specs/009-repo-docs-update/quickstart.md to confirm: all 7 READMEs exist, root README links to all courses, LinkedIn summary preserved, shared setup preserved, LangGraph pattern docs moved, MCP links to sub-project READMEs, consistent structure, no broken markdown.

**Checkpoint**: All READMEs are consistent and all validation scenarios pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (Phase 1)**: No dependencies — can start immediately. All 7 READMEs are independent (different files).
- **User Story 2 (Phase 2)**: Depends on US1 being partially complete (needs to know what content goes in LangGraph README to move pattern docs). T009 should run after T001.
- **User Story 3 (Phase 3)**: Depends on US1 and US2 being complete (audits all READMEs for consistency).

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately — no dependencies on other stories
- **User Story 2 (P2)**: Can start after T001 (LangGraph README exists to receive moved content)
- **User Story 3 (P3)**: Depends on US1 + US2 completion (consistency audit requires all READMEs to exist)

### Parallel Opportunities

- **Within US1**: All 7 README creation tasks (T001-T007) can run in parallel — they write to different files with no dependencies on each other
- **Between stories**: US2 can start as soon as T001 completes (pattern docs need a destination). US3 must wait for all other stories.

---

## Parallel Example: User Story 1

```bash
# Launch all 7 README creation tasks together:
Task: "Create LangGraph Framework course README in src/langgraph_course/README.md"
Task: "Create Multi-Agent Design & Governance course README in src/multiagent-governance_course/README.md"
Task: "Create Building AI Agents for Complex Tasks course README in src/building-ai-agents-for-complex-tasks/README.md"
Task: "Create Advanced Multi-Agent AI Systems course README in src/advanced-multi-agent-ai-system-course/README.md"
Task: "Create MCP course README in src/mcp-model-content-protocol-course/README.md"
Task: "Create Agentic AI Protocols course README in src/agentic-ai-protocols-mcp-a2a-acp-course/README.md"
Task: "Create Ethical Governance & Risk course README in src/ethical-governance--risk-in-agentic-ai-course/README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create all 7 course READMEs (T001-T007) — can be done in parallel
2. **STOP and VALIDATE**: Verify each README exists and is self-contained
3. Deploy/demo if ready — each course now has standalone documentation

### Incremental Delivery

1. Complete US1 → 7 course READMEs exist and are self-contained (MVP!)
2. Add US2 → Root README becomes navigation hub, pattern docs move to LangGraph README
3. Add US3 → All READMEs normalized for consistency, all validation scenarios pass
4. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a documentation-only feature — no code, no tests, no configuration changes
- Total tasks: 11 (7 for US1, 2 for US2, 2 for US3)
- Estimated effort: ~2-3 hours for a single implementer, ~1 hour with parallel execution
