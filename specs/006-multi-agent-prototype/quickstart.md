# Quickstart: Multi-Agent Research Assistant Prototype

## Prerequisites

- Python 3.10+
- Poetry installed
- `.env` configured with an LLM provider (project standard via `src/config.py:Settings`). For offline/mock runs, LLM calls fall back to deterministic extraction — no API key required for the mock sample query.
- Dependencies installed: `poetry install`

## Setup

```bash
# Install (if pyproject.toml was updated with the new package, re-install)
poetry install

# Verify imports
poetry run python -c "from research_assistant_prototype.graph import run_research; print('ok')"
```

## Validation Scenarios

### Scenario 1: Full end-to-end — sample research query → synthesized report

**Goal**: Verify FR-001..FR-009, FR-015, SC-001/SC-002/SC-003/SC-005.

```bash
poetry run python -c "
from research_assistant_prototype.graph import run_research

state = run_research(
    topic='What are the latest advances in transformer efficiency for low-resource languages?',
    domain_tags=['NLP', 'transformers', 'low-resource'],
    max_execution_minutes=5,
)
print('Status:', state.request.status)
print('Sources:', len(state.source_records), 'credibility flags:', {s.credibility_flag for s in state.source_records})
print('Findings by agent:', {k: len(v) for k, v in state.agent_outputs.items()})
print('Report sections:', len(state.report.sections) if state.report else 0)
print('Processing outcome:', state.report.processing_outcome if state.report else 'n/a')
print('Telemetry events:', len(state.telemetry_events))
print('Conflicts:', len(state.conflicts))
"
```

**Expected**: Status `completed`; ≥5 sources each with credibility flag (SC-003); findings from literature_search/analysis/citation_verification; `report.sections` ≥1 with `provenance_trace`; one telemetry event per agent (SC-005); outcome `complete`.

---

### Scenario 2: Broad/empty query → needs_refinement

**Goal**: Verify router validation (Edge Case: too broad) and FR-003 guard.

```bash
poetry run python -c "
from research_assistant_prototype.graph import run_research

state = run_research(topic='tell me about science', domain_tags=[])
print('Status:', state.request.status)
print('Expected: needs_refinement')
print('Sources:', len(state.source_records))
"
```

**Expected**: Status `needs_refinement`; no sources or findings produced; report is `None`.

---

### Scenario 3: Empty literature results → graceful data-gap disclosure

**Goal**: Verify Edge Case (zero papers) and FR-014 / SC-006.

```bash
poetry run python -c "
from research_assistant_prototype.graph import run_research

# Use a nonsensical topic that yields no mock matches (implementation will emit gap finding)
state = run_research(
    topic='zzzzzzz nonexistent topic with no mock sources',
    domain_tags=['zzz'],
    max_execution_minutes=2,
)
print('Status:', state.request.status)
print('Sources:', len(state.source_records))
print('Data gaps:', state.report.data_gaps if state.report else [])
print('Outcome:', state.report.processing_outcome if state.report else 'n/a')
"
```

**Expected**: Report exists with `data_gaps` documenting insufficient sources; outcome `partial` is acceptable; no unhandled exception.

---

### Scenario 4: Conflict detection and resolution

**Goal**: Verify FR-012 / SC-004.

```bash
poetry run python -c "
from research_assistant_prototype.graph import run_research

state = run_research(
    topic='What are the latest advances in transformer efficiency for low-resource languages?',
    domain_tags=['NLP', 'transformers'],
    constraints={'seed_conflicts': True},
    max_execution_minutes=5,
)
if state.conflicts:
    for c in state.conflicts:
        print(f'Conflict on {c.dimension}: {c.description} | status={c.resolution_status}')
    print('Conflict disclosures in report:', len(state.report.conflict_disclosures) if state.report and state.report.conflict_disclosures else 0)
else:
    print('No conflicts detected (agents agreed)')
"
```

**Expected**: Conflicts detected when seeded; each has `resolution_status` of `resolved` or `escalated`; escalated conflicts appear in `report.conflict_disclosures`. SC-004 requires 100% of conflicts to be either resolved or surfaced.

---

### Scenario 5: Graceful degradation — forced agent failure

**Goal**: Verify FR-014 / SC-006 (partial outcome, not crash).

```bash
poetry run python -c "
from research_assistant_prototype.graph import run_research

state = run_research(
    topic='What are the latest advances in transformer efficiency for low-resource languages?',
    domain_tags=['NLP'],
    constraints={'simulate_failure_roles': ['analysis']},
    max_execution_minutes=5,
)
print('Outcome:', state.report.processing_outcome if state.report else 'n/a')
print('Data gaps:', state.report.data_gaps if state.report else [])
print('Error records:', state.error_records)
print('Other agents still produced:', any(len(v)>0 for k,v in state.agent_outputs.items() if k != 'analysis'))
"
```

**Expected**: Outcome `partial`; `data_gaps` mentions analysis; `error_records` contains an entry for the failed step; other agents still produced output.

---

### Scenario 6: Execution budget enforcement

**Goal**: Verify budget handling (Edge Case: runaway agent).

```bash
poetry run python -c "
import time
from research_assistant_prototype.graph import run_research

start = time.monotonic()
state = run_research(
    topic='What are the latest advances in transformer efficiency for low-resource languages?',
    domain_tags=['NLP'],
    max_execution_minutes=1,  # very tight budget
)
elapsed = time.monotonic() - start
print(f'Elapsed: {elapsed:.1f}s  Expected < 90s')
print(f'Stop reason: {state.execution_metadata.get(\"stop_reason\", \"unknown\")}')
print(f'Status: {state.request.status}')
print(f'Outcome: {state.report.processing_outcome if state.report else \"n/a\"}')
"
```

**Expected**: Completes within ~90s; `stop_reason` is `max_budget` or `budget_forced_synthesis`; report exists (possibly partial).

---

## Generating Submission Artifacts

```bash
# Sample output
poetry run python -m research_assistant_prototype.artifacts.sample_output
# -> docs/006-prototype/sample_output.md

# Architecture diagram
poetry run python -m research_assistant_prototype.artifacts.diagram
# -> docs/006-prototype/architecture_diagram.png (+ .mmd source)

# Reflection is committed as docs/006-prototype/reflection.md
```

## Running Tests

```bash
poetry run python -m unittest discover -v tests/research_assistant_prototype/
```

**Expected**: All unit, contract, and integration tests pass. Tests requiring LLM may skip gracefully when no API key is configured (mock fallback).

## Key Contracts

- Agent interfaces: [contracts/agent-interfaces.md](contracts/agent-interfaces.md)
- Public entry points: [contracts/api-contracts.md](contracts/api-contracts.md)
- Data model: [data-model.md](data-model.md)
