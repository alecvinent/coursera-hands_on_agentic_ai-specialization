# Research: Multi-Agent Research Assistant Prototype

## Design Decisions

### Decision 1: Framework selection (LangGraph vs CrewAI vs AutoGen)

- **Decision**: Use **LangGraph** (`StateGraph` + `pydantic.BaseModel` state) as the orchestration layer. If a future extension requires agent-to-agent autonomy dialogue, wrap it inside a LangGraph node rather than switching frameworks.
- **Rationale**: The project constitution (Article I) mandates LangGraph primitives as the sole orchestration layer for inspectability, serialization, and LangSmith tracing. The PDF permits CrewAI or AutoGen, but the constitution supersedes and defaults to LangGraph unless a documented justification exists — none does for this prototype's sequential pipeline.
- **Alternatives considered**: CrewAI (role-based crews with built-in tool calling) — violates constitution I and hides graph topology; AutoGen (conversational agents) — over-engineered for a 3-4 agent pipeline with structured handoffs. Both deferred to future work and documented in reflection if revisited.

### Decision 2: Agent specialization and count

- **Decision**: **4 agents** — Literature Search (mandatory), Analysis (mandatory), Citation Verification (optional, satisfies FR-010), Synthesis (mandatory, terminal). Each has a distinct input/output schema and responsibility description per FR-002.
- **Rationale**: The PDF requires at least 3 (Literature Search, Analysis, Synthesis) and suggests Citation Verification or Quality Assessment as the optional fourth. Choosing Citation Verification directly exercises provenance and credibility (FR-011) and is more concrete to test than a generic QualityAssessment. 4 agents prove task decomposition without inflating scope.
- **Alternatives considered**: 3 agents only (meets minimum but leaves FR-010 to be justified in docs — weaker submission); 5 agents (Quality Assessment + Citation Verification) — adds scope without additional evaluation signal for the prototype.

### Decision 3: Coordination topology

- **Decision**: **Sequential pipeline with conditional edges**: `validate_request → literature_search → analysis → citation_verification → synthesis`, plus two conditional branches: (a) `validate_request` can route to `needs_refinement` (broad/empty query guard), and (b) `citation_verification` can route directly to `synthesis` via a budget/confidence trigger. No cyclic loop — Synthesis is terminal via `set_finish_point`.
- **Rationale**: Sequential ordering guarantees downstream agents see upstream outputs (FR-006 context preservation) with zero ambiguity. Conditional edges handle governance (validation, budget) without hard-coded branching inside nodes (constitution I). A cyclic loop (as in module_3 `multi_agent_research` and capstone 002) is unnecessary for a single-pass research summary and would complicate budget enforcement.
- **Alternatives considered**: Parallel fan-out (literature + analysis concurrently) — analysis depends on literature results, so parallelism is false; fully orchestrator-mediated delegation (market pattern) — over-engineered for 4 nodes; cyclic refinement loop — adds iteration budget complexity for marginal gain in a mock-data prototype.

### Decision 4: Mock literature retrieval and source metadata

- **Decision**: Implement a **deterministic mock retrieval** layer in `nodes/literature_search.py` that returns 5-8 curated `SourceRecord` entries matching the query's domain tags, each with title, authors, venue, year, abstract/snippet, credibility score, relevance score, and retrieval timestamp. Venue tiers drive credibility (e.g., Nature/Science 0.95, peer-reviewed journal 0.85, preprint 0.65, blog 0.25). Mock data is keyed by query keywords so the sample query ("transformer efficiency low-resource languages") always yields plausible results. Real API replacement path is documented in code comments.
- **Rationale**: PDF explicitly permits mock APIs and instructs to focus on multi-agent principles over perfect functionality (FR-020). Deterministic mocks make tests reproducible (SC-008) and avoid external API flakiness. Structured metadata satisfies FR-007 and feeds credibility/conflict logic.
- **Alternatives considered**: Live arXiv/Semantic Scholar API — violates mock allowance, introduces network dependency and rate limits; LLM-generated sources — risks hallucinated citations that would fail credibility checks; empty passthrough — fails FR-007's structured metadata requirement.

### Decision 5: Credibility scoring and conflict resolution

- **Decision**: **Credibility**: rule-based heuristic in `literature_search` — `score = venue_tier_weight * 0.5 + recency_weight * 0.2 + citation_count_weight * 0.2 + domain_match * 0.1`, clamped 0-1, with a flag threshold at 0.4 (below → flagged `low_credibility`). **Conflict detection**: compare `Finding` pairs sharing dimension tags or source overlap with contradictory numeric/textual claims; rule-based overlap in `coordination/conflict.py`. **Resolution**: if confidence delta >0.25, prefer higher-confidence finding; otherwise surface both perspectives with `resolution_status=escalated` and disclose in synthesis.
- **Rationale**: Satisfies FR-011 (credibility signal on every source, SC-003) and FR-012/ SC-004 (100% of conflicts either resolved or transparently surfaced). Rule-based approach is cheap, deterministic, and testable without an LLM judge in the prototype; an LLM-based tie-breaker is noted as a future enhancement in the reflection.
- **Alternatives considered**: Pure LLM credibility judge — adds cost and non-determinism for a mock-data prototype; citation-graph lookup — requires real API; skipping conflict detection — violates FR-012.

### Decision 6: Observability, error handling, and execution budget

- **Decision**: **Observability**: `@timed_node('node_name')` decorator (or manual `time.monotonic()` for plain functions per `utils/decorators.py` note) on every node, `loguru` for structured logs, `list[ErrorRecord]` (TypedDict: step, error_type, message, timestamp) and `list[TelemetryEvent]` accumulated in `SharedState`. **Error handling**: exponential backoff retry (2 retries, base 0.5s) for transient LLM failures; on exhaustion, emit `ErrorRecord`, mark agent `FAILED`, and allow synthesis to produce `processing_outcome="partial"` with a `data_gaps` section. **Budget**: `time.monotonic()` compared to `execution_metadata["max_execution_minutes"]` at each routing decision; at 80% consumption, force `synthesize` with available data (same pattern as capstone 002).
- **Rationale**: Directly satisfies constitution Article III (observability), FR-013 (telemetry per activation, SC-005), FR-014 (typed errors + partial outcome, SC-006), and FR-004/FR-015 (controlled autonomy with bounded execution). Reuses proven patterns from `module_3/labs/multi_agent_research` and `002-multi-agent-capstone`.
- **Alternatives considered**: OpenTelemetry SDK — new dependency, unjustified per Article VI; LangSmith-only tracing — not always available in evaluation; hard interrupt via signals — platform-dependent and loses state capture.

### Decision 7: Submission artifacts (diagram, sample output, reflection, documentation)

- **Decision**: **Architecture diagram**: generated by `artifacts/diagram.py` using `grandalf` for layout or Mermaid HTML fallback; version-controlled as `docs/006-prototype/architecture_diagram.png` (and `.mmd` source). Depicts agent roles, communication flows (shared state edges), and coordination pattern (sequential + conditionals). **Sample output**: `artifacts/sample_output.py` runs `run_research(topic="What are the latest advances in transformer efficiency for low-resource languages?", domain_tags=["NLP","transformers","low-resource"], max_execution_minutes=5)` and writes `docs/006-prototype/sample_output.md` with intermediate agent contributions and final synthesis. **Reflection**: `docs/006-prototype/reflection.md`, 400-600 words, covering framework choice, pipeline vs hierarchical reasoning, mock boundary, credibility trade-offs, and two scaling improvements (live APIs, hierarchical delegation). **Code docs**: inline comments on every node explaining design decisions per PDF technical notes.
- **Rationale**: Satisfies FR-017/FR-018/FR-019 and SC-007/SC-008. Grandalf and pymupdf are already in the approved stack, so no new deps. Generating artifacts from code guarantees they stay in sync with the implementation.
- **Alternatives considered**: Hand-drawn diagram (not regeneratable); Streamlit UI for sample output — the spec does not require a UI and would add scope; embedding artifacts only in `specs/` — `docs/` keeps submission artifacts discoverable.
