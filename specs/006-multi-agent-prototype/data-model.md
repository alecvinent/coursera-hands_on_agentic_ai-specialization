# Data Model: Multi-Agent Research Assistant Prototype

## Entity: ResearchQuery (alias ResearchRequest)

The academic question or topic submitted as input.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| topic | str | Raw research question text | Required, 1-500 chars, non-whitespace |
| domain_tags | list[str] | Domain hints (e.g., "NLP", "transformers", "low-resource") | Optional; if provided, at least 1 tag; used by mock retrieval |
| constraints | dict[str, Any] | Optional filters: date_range, venue_filter, max_sources | Optional |
| status | enum | pending, active, completed, failed, needs_refinement | Default: pending |

**State transitions**: pending → active (validation pass) → completed (synthesis done); pending → needs_refinement (too broad/empty); active → failed (unrecoverable error before synthesis).

**Validation notes**: Topic length <10 chars and no domain_tags → treated as too broad (see router validation). FR-003 decomposition depends on tags.

---

## Entity: SourceRecord

A retrieved academic source returned by Literature Search.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str | Unique source identifier | Auto UUID |
| title | str | Paper title | Required, non-empty |
| authors | list[str] | Author names | At least 1 |
| venue | str | Journal/conference/preprint/blog name | Required |
| year | int | Publication year | 1900-2030 |
| abstract | str | Abstract or snippet | Required |
| credibility_score | float | 0.0-1.0 heuristic (venue tier + recency + citations + domain match) | Required, 0.0-1.0 |
| credibility_flag | str | "verified" or "low_credibility" | Derived: score <0.4 → low_credibility |
| relevance_score | float | Query-source relevance | Required, 0.0-1.0 |
| retrieved_at | datetime | Retrieval timestamp | Auto UTC |

**Relationships**: Produced by Literature Search; consumed by Analysis and Citation Verification; linked from Findings via `source_id`.

---

## Entity: Finding (Insight)

An atomic piece of information extracted by Analysis (and enriched by Citation Verification).

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str | Unique finding identifier | Auto UUID |
| agent_role | str | Which agent produced this | Required (analysis, citation_verification) |
| content | str | The finding text | Required, non-empty |
| source_ids | list[str] | SourceRecord IDs it is derived from | At least 1; provenance |
| source | str | Human-readable attribution (e.g., "Smith et al. 2024, Nature") | Required |
| confidence | float | Confidence score | Required, 0.0-1.0 |
| dimension_tags | list[str] | Semantic dimensions (e.g., "efficiency", "low-resource", "quantization") | Optional, used by conflict detection |
| timestamp | datetime | When created | Auto UTC |
| provenance_chain | list[str] | IDs of upstream findings this is derived from | Optional |
| cross_references | list[str] | IDs of related findings from other agents | Optional, populated by coordination |

---

## Entity: Conflict

A detected contradiction between two or more Findings.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| finding_ids | list[str] | Conflicting finding IDs | At least 2 |
| dimension | str | Semantic dimension of conflict | Required |
| description | str | Nature of the contradiction | Required |
| detected_at | datetime | When detected | Auto UTC |
| resolution_status | enum | unresolved, resolved, escalated | Default: unresolved |
| resolution_rationale | str | How resolved or why escalated | Optional, required if resolved/escalated |
| resolution_method | str | rule-based, confidence-comparison | Optional |

**State transitions**: unresolved → resolved (confidence delta >0.25, higher-confidence wins) → escalated (delta ≤0.25, both perspectives surfaced).

---

## Entity: AgentState

Per-agent execution state tracked in SharedState.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| role | enum | literature_search, analysis, citation_verification, synthesis | Required |
| execution_state | enum | idle, running, completed, failed | Default: idle |
| input_requirements | list[str] | Upstream roles this agent depends on | Optional |
| findings | list[Finding] | Findings produced by this agent (also mirrored in agent_outputs) | Starts empty |
| confidence | float | Aggregate confidence | 0.0-1.0 |
| latency_ms | float | Last execution latency | ≥0, set by @timed_node |

---

## Entity: SharedState (Graph State)

Top-level `pydantic.BaseModel` used as `StateGraph` state schema.

| Field | Type | Description |
|-------|------|-------------|
| request | ResearchQuery | Original query + decomposed scope |
| source_records | list[SourceRecord] | All retrieved sources (credibility-scored) |
| agent_outputs | dict[str, list[Finding]] | Per-agent findings keyed by role |
| agent_states | dict[str, AgentState] | Per-agent execution state |
| conflicts | list[Conflict] | Detected and resolved conflicts |
| cross_agent_insights | list[str] | Emergent connections between agents' findings |
| error_records | list[ErrorRecord] | Typed errors (step, error_type, message, timestamp) |
| telemetry_events | list[TelemetryEvent] | Operational events per activation |
| execution_metadata | dict[str, Any] | workflow_start (monotonic), max_execution_minutes, stop_reason, processing_outcome, degraded_agents |
| report | ResearchSummary \| None | Final output (null until synthesis completes) |
| messages | Annotated[list, add_messages] | LangGraph message accumulator for tracing |
| steering_instructions | list[dict] | Reserved for future human-in-the-loop (not required for v1) |

**Reducers**: `messages` uses `add_messages`; all other fields are overwrite/append as defined by Pydantic model.

---

## Entity: ResearchSummary (Synthesized Output)

Final deliverable produced by Synthesis.

| Field | Type | Description |
|-------|------|-------------|
| sections | list[dict] | Narrative sections: {title, body, finding_ids[]} |
| cross_references | list[dict] | Explicit connections between findings from different agents |
| conflict_disclosures | list[Conflict] | Conflicts surfaced when escalated |
| data_gaps | list[str] | Areas where an agent was bypassed or produced no findings |
| provenance_trace | dict[str, Any] | Mapping claim → Finding ID → SourceRecord → AgentRole |
| processing_outcome | str | "complete" or "partial" (partial when synthesis used incomplete inputs) |
| generated_at | datetime | When finalized |

---

## Entity: TelemetryEvent

| Field | Type | Description |
|-------|------|-------------|
| event_type | enum | agent_latency, output_confidence, conflict_detected, failure, stop_triggered |
| agent_role | str | Which agent triggered this |
| value | float | Numeric value (latency ms, confidence, count) |
| details | dict[str, Any] | Extra context (error message, retry count, stop reason) |
| timestamp | datetime | Auto UTC |

---

## Entity: ErrorRecord (TypedDict)

| Field | Type | Description |
|-------|------|-------------|
| step | str | Agent or coordinator step name |
| error_type | str | e.g., "llm_timeout", "empty_sources", "credibility_failure", "citation_unverifiable" |
| message | str | Human-readable error description |
| timestamp | str | ISO 8601 UTC |

**Note**: Stored as `list[ErrorRecord]` (TypedDict) per constitution Article III — not a BaseModel — to keep the error surface minimal and serializable.

---

## State Transitions (Summary)

```
ResearchQuery.status:
  pending → active (validate_query passes)
  pending → needs_refinement (topic too broad/empty)
  active → completed (synthesis produced, outcome complete or partial)
  active → failed (unrecoverable error before synthesis)

AgentState.execution_state:
  idle → running (activated by graph edge)
  running → completed (findings produced, including empty-but-documented)
  running → failed (exception or empty output with error record)

Conflict.resolution_status:
  unresolved → resolved (confidence delta >0.25)
  unresolved → escalated (delta ≤0.25, both views surfaced)

ResearchSummary.processing_outcome:
  "complete" (all non-optional agents succeeded)
  "partial" (≥1 agent failed or budget forced early synthesis)
```
