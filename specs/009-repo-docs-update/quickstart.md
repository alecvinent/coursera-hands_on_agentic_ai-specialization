# Quickstart Validation: Course README & General README Update

**Date**: 2026-09-20
**Feature**: 009-repo-docs-update

## Prerequisites

- Git repository cloned locally
- No code dependencies needed (documentation-only change)

## Validation Scenarios

### Scenario 1: All 7 Course READMEs Exist

**Setup**: Navigate to repository root.

**Command**:
```bash
find src/ -maxdepth 2 -name "README.md" -type f | sort
```

**Expected outcome**: 7 files listed, one in each course directory:
```
src/advanced-multi-agent-ai-system-course/README.md
src/agentic-ai-protocols-mcp-a2a-acp-course/README.md
src/building-ai-agents-for-complex-tasks/README.md
src/ethical-governance--risk-in-agentic-ai-course/README.md
src/langgraph_course/README.md
src/mcp-model-content-protocol-course/README.md
src/multiagent-governance_course/README.md
```

---

### Scenario 2: Root README Links to All Courses

**Setup**: Open `README.md` at repo root.

**Command**: Visual inspection or grep for course links.

```bash
grep -c "src/.*/README.md" README.md
```

**Expected outcome**: At least 7 matches (one link per course).

---

### Scenario 3: Root README Preserves LinkedIn Summary

**Setup**: Open `README.md` at repo root.

**Command**:
```bash
grep -c "LinkedIn Summary" README.md
```

**Expected outcome**: 1 match.

---

### Scenario 4: Root README Preserves Shared Setup

**Setup**: Open `README.md` at repo root.

**Command**:
```bash
grep -E "(Prerequisites|poetry install|\.env)" README.md | head -5
```

**Expected outcome**: Lines mentioning Python 3.10+, Poetry install, and .env configuration.

---

### Scenario 5: LangGraph Pattern Docs Moved

**Setup**: Verify pattern content is in LangGraph course README, not root.

**Command**:
```bash
grep -c "Coordinator Pattern\|Specialist Pattern\|Event-Driven\|ReAct Pattern\|Reflection Pattern\|Planning Pattern\|Tool Pattern\|Sequential Pattern\|Human-in-the-Loop" README.md
```

**Expected outcome**: 0 matches in root README (moved to LangGraph course README).

```bash
grep -c "Coordinator Pattern\|Specialist Pattern\|Event-Driven\|ReAct Pattern\|Reflection Pattern\|Planning Pattern\|Tool Pattern\|Sequential Pattern\|Human-in-the-Loop" src/langgraph_course/README.md
```

**Expected outcome**: 9+ matches in LangGraph course README.

---

### Scenario 6: MCP Course Links to Sub-Project READMEs

**Setup**: Open `src/mcp-model-content-protocol-course/README.md`.

**Command**:
```bash
grep -c "module_3/task.*README" src/mcp-model-content-protocol-course/README.md
```

**Expected outcome**: At least 2 matches (links to task1 and task2 READMEs, not duplicated content).

---

### Scenario 7: Consistent Structure Across READMEs

**Setup**: Compare section headings across all per-course READMEs.

**Command**:
```bash
for f in src/*/README.md; do echo "=== $f ==="; grep "^## " "$f"; done
```

**Expected outcome**: Each README contains at minimum: `## Modules`, `## Setup`, `## Running` (or equivalent).

---

### Scenario 8: No Broken Markdown

**Setup**: Check for common markdown issues.

**Command**:
```bash
for f in README.md src/*/README.md; do echo "=== $f ==="; grep -n "^\[" "$f" | grep -v "](http" | head -3; done
```

**Expected outcome**: No orphaned link text (all `[text]` followed by `(url)`).

---

## Regression Check

Ensure no content was accidentally deleted from the root README:

```bash
wc -l README.md
```

**Expected outcome**: Root README should be shorter than 852 lines (content moved to LangGraph README) but still substantial (~150-250 lines as a hub).
