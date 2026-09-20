# API Contracts: Research Assistant Prototype

## Public Entry Points

### `run_research(topic, domain_tags, constraints, max_execution_minutes) -> SharedState`

The primary synchronous entry point (analogous to `module_3/labs/multi_agent_research/graph.py:run_research`).

```python
from research_assistant_prototype.graph import run_research

state = run_research(
    topic="What are the latest advances in transformer efficiency for low-resource languages?",
    domain_tags=["NLP", "transformers", "low-resource"],
    constraints={"max_sources": 8},
    max_execution_minutes=5,
)

# Inspect results
print(state.request.status)           # "completed" or "needs_refinement" or "failed"
print(len(state.source_records))      # >=5 for the sample query (SC-003)
print(state.report.sections)          # narrative sections (SC-002)
print(state.report.processing_outcome) # "complete" or "partial" (SC-006)
print(state.telemetry_events)         # one per agent (SC-005)
print(state.error_records)            # typed errors if any (FR-014)
```

**Request contract**:
- `topic: str` — required, 1-500 chars. Empty or whitespace → validation path.
- `domain_tags: list[str] | None` — optional. Empty list treated as no tags.
- `constraints: dict | None` — optional (e.g., `{"max_sources": 8, "simulate_failure_roles": ["analysis"]}` test hook).
- `max_execution_minutes: int` — default 5, max 30.

**Response contract** (`SharedState`):
- `request.status: str` — `completed` (normal), `needs_refinement` (broad/empty query), `failed` (unrecoverable).
- `source_records: list[SourceRecord]` — every entry has `credibility_score` and `credibility_flag`.
- `report: ResearchSummary | None` — `None` only when status is `needs_refinement` or `failed`; otherwise populated with `sections`, `cross_references`, `conflict_disclosures`, `data_gaps`, `provenance_trace`.
- `telemetry_events: list[TelemetryEvent]` — at least one per executed agent.
- `error_records: list[ErrorRecord]` — empty on success; populated on degraded runs.

**Error contract**: Never raises on degraded agent failure — returns `processing_outcome="partial"` instead (SC-006). Only raises on programming errors (invalid topic type).

---

### `stream_research(topic, domain_tags, constraints, max_execution_minutes) -> Iterator[tuple[str, SharedState]]`

Streaming variant for UI integration. Yields `(node_name, state_snapshot)` per graph step.

```python
from research_assistant_prototype.graph import stream_research

for node_name, snapshot in stream_research(topic="...", domain_tags=[...]):
    print(f"[{node_name}] status={snapshot.request.status}")
```

Yield order: `validate_request` → `literature_search` → `analysis` → `citation_verification` → `synthesize`.

---

### CLI / Script entry point

```bash
# Run the sample query and write docs/006-prototype/sample_output.md
poetry run python -m research_assistant_prototype.artifacts.sample_output

# Generate the architecture diagram
poetry run python -m research_assistant_prototype.artifacts.diagram
```

---

### Validation hooks (for tests only)

The `constraints` dict supports test-only simulation flags (not part of the public researcher contract):

| Flag | Effect |
|------|--------|
| `simulate_failure_roles: list[str]` | Force listed agent roles to emit FAILED state |
| `seed_conflicts: bool` | Seed contradictory findings to exercise conflict detection |

These flags are ignored in normal usage and documented as test scaffolding.
