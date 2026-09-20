# Agent Interface Contracts: Research Assistant Prototype

## Node Function Signature

Every LangGraph node follows:

```python
def node_fn(state: SharedState) -> SharedState:
    ...
```

Nodes receive the full `SharedState` (Pydantic BaseModel) and return the updated state with contributions appended. No node mutates state in place — updates are returned.

Nodes are decorated with `@timed_node("node_name")` where classmethod signature allows it; otherwise manual `time.monotonic()` latency is recorded into `telemetry_events` and `agent_states[role].latency_ms`.

---

## Agent Contract: LiteratureSearchAgent

**Role**: Retrieve (mock) academic sources relevant to the research query.

- **Input requirements**: `request` (topic, domain_tags, constraints).
- **Output**: Appends `SourceRecord` entries to `state.source_records` (5-8 entries). Each record carries `credibility_score`/`credibility_flag` and `relevance_score`. Also appends 0 findings to `agent_outputs["literature_search"]` (sources are the output; findings are produced downstream).
- **Triggered by**: `validate_request` passing (topic not flagged as needs_refinement).
- **Signals**: Publishes `source_records` with credibility flags; tags each record's `retrieved_at`.
- **Failure mode**: On retrieval failure, emits `ErrorRecord{step="literature_search", error_type="retrieval_failure", ...}` and returns state with `agent_states["literature_search"].execution_state=FAILED` and `execution_metadata["degraded_agents"]` updated. Synthesis can still run with partial data.
- **Mock boundary**: Deterministic keyword → curated sources mapping. Replace with `arXiv`/`Semantic Scholar` client behind the same interface.

## Agent Contract: AnalysisAgent

**Role**: Extract key insights, data points, and thematic findings from `SourceRecord`s.

- **Input requirements**: `source_records` (from Literature Search). Reads `request` for scope.
- **Output**: Produces `Finding` entries under `agent_outputs["analysis"]` with `source_ids` provenance, `confidence`, and `dimension_tags` (e.g., "efficiency", "quantization", "low-resource"). Optionally uses `LLMFactory` to summarize abstracts into findings; fallback is template extraction for deterministic tests.
- **Triggered by**: Completion of `literature_search` (or after budget check if degraded).
- **Signals**: Cross-references findings via `provenance_chain` and `source_ids`.
- **Failure mode**: If `source_records` is empty, emits `ErrorRecord{error_type="empty_sources"}` and produces a single `Finding` documenting the gap (confidence 0.0) so synthesis can disclose it. On LLM failure, retries with backoff, then marks FAILED.

## Agent Contract: CitationVerificationAgent (Optional, FR-010)

**Role**: Verify and flag citations/provenance of Analysis findings and source credibility.

- **Input requirements**: `source_records` + `agent_outputs["analysis"]`.
- **Output**: Enriches findings with verification flags; appends `Finding` entries under `agent_outputs["citation_verification"]` indicating verified vs unverifiable citations. May add new `Conflict` entries for unverifiable claims.
- **Triggered by**: Completion of `analysis`. Can be skipped via config flag if only 3 agents are desired (documented in reflection).
- **Signals**: Attaches verification status to `source_records` credibility flags; flags unverifiable citations for disclosure in synthesis.
- **Failure mode**: On failure, emits `ErrorRecord{error_type="citation_unverifiable"}` and proceeds — synthesis surfaces unverified citations as gaps.

## Agent Contract: SynthesisAgent (Terminal)

**Role**: Combine literature results, analysis insights, and verification flags into a coherent research summary.

- **Input requirements**: `source_records` + all `agent_outputs` + `conflicts` + `error_records` + `execution_metadata`.
- **Output**: Sets `state.report: ResearchSummary` with `sections`, `cross_references`, `conflict_disclosures`, `data_gaps`, `provenance_trace`, `processing_outcome` ("complete" or "partial"), and `generated_at`. Sets `request.status` to `completed`.
- **Triggered by**: Last in pipeline after `citation_verification` (or `analysis` if optional agent skipped), or forced by budget check at 80% consumption.
- **Signals**: Final deliverable for the user; cross-references findings from multiple agents (SC-002); includes conflict disclosures and data gaps.
- **Failure mode**: If all upstream agents failed, produces minimal `ResearchSummary` with `processing_outcome="partial"` and `data_gaps` documenting missing inputs rather than throwing.

---

## Coordination Contract: Router

**Decision points**:

| Router | Input | Output | Destination |
|--------|-------|--------|-------------|
| `validate_query` | `state.request` (topic, domain_tags) | `"needs_refinement"` if topic <10 chars and no domain_tags, or topic is empty/whitespace | `needs_refinement` node → then `literature_search` |
| `validate_query` | — | `"run_research"` otherwise | `literature_search` |
| `check_execution_budget` | `execution_metadata.workflow_start`, `max_execution_minutes` | `True` if elapsed >= max_execution_minutes or >=80% budget without synthesis | Force `synthesize` |
| `should_synthesize` | agent completion state | `"synthesize"` when pipeline complete or budget trigger | `synthesize` (terminal) |

**Budget enforcement**: `time.monotonic()` comparison against `max_execution_minutes` (default 5 for mock runs, configurable via `Settings`). Checked before each transition.

---

## Coordination Contract: ConflictResolver

- **Detection** (`coordination/conflict.py:detect_conflicts`): Compares all `Finding` pairs with overlapping `dimension_tags` or shared `source_ids`; flags as conflict if textual claims differ or numeric values diverge beyond threshold.
- **Resolution** (`coordination/conflict.py:resolve_conflicts`): For each conflict, if `max_confidence - min_confidence > 0.25`, higher-confidence finding wins (`resolved`). Otherwise `escalated` — both perspectives preserved and appended to `state.conflicts` for disclosure in `ResearchSummary.conflict_disclosures`.
- **Logging**: Each detection/resolution emits a `TelemetryEvent{event_type="conflict_detected"}` and is recorded in `state.conflicts`.
