**Q1: What’s one design decision you're most proud of?**

The design decision I am most proud of is implementing an **isolated, pre-execution fallback and exception-interception layer** directly between the deliberative planner and external tool execution webhooks.

### Architectural Structure & Mechanics

Rather than allowing the LLM agent to call external APIs directly or letting tools execute side effects immediately upon plan generation, all tool calls are wrapped in a synchronous state-validation pipeline:

$$\text{Planner Intent} \longrightarrow \mathbf{\text{[ Pre-Execution Interceptor ]}} \longrightarrow \begin{cases} \text{Execute Tool} & \text{(Validation Passed)} \\ \text{Self-Correction Loop} & \text{(Ambiguity / Soft Error)} \\ \text{Human Escalation} & \text{(System / API Error)} \end{cases}$$

Before dispatching an order payload to external APIs (e.g., inventory deduction or messaging webhooks), the interceptor executes two deterministic checks:

1. **Schema & State Verification:** Validates that all required fields are present, correctly typed, and within business rules (e.g., non-zero item quantities, valid business hours).
2. **Circuit Breaker & Fallback Wrapper:** Catches API timeouts, database dropouts, or out-of-stock signals before any side effect is committed.

### Design Trade-Offs & Alternatives Considered

When designing this architecture, I evaluated three primary structural patterns:

* **Direct LLM Tool Calling (Rejected):** Allowing the planner to call external webhooks directly minimizes latency but risks executing irreversible side effects (like sending partial orders or duplicate billing calls) whenever the LLM hallucinates arguments or encounters an unhandled API error.
* **Post-Execution Rollbacks (Rejected):** Executing tool calls immediately and attempting compensating transactions (rollbacks) upon failure added significant implementation complexity and created window vulnerabilities where external services (like messaging APIs) had already notified the customer before the failure was detected.
* **Pre-Execution Interception Layer (Chosen):** While this adds a minor computational step before tool invocation, it guarantees transactional safety and complete deterministic control over external side effects.

### Practical Impact & Concrete Scenario

In practice, this architecture protects system robustness and user trust in dynamic real-world environments:

* **Concrete Scenario:** A customer requests an order during a brief inventory API timeout. Instead of allowing a broken payload to trigger a partial WhatsApp notification or crashing the session mid-conversation, the interceptor catches the `503 Service Unavailable` error silently. It halts the external webhook, updates short-term session memory with an `ESCALATED` flag, and routes the request to human staff with full conversational context attached. The customer receives a polite message informing them that a team member is finalizing their request manually, preserving operational continuity and customer trust.

### Alignment with Course Learning Objectives

This design explicitly integrates several core course pillars into a single resilient system:

* **Tool Integration & Reliability:** Treats tools not as omniscient black boxes, but as uncertain external dependencies requiring strict defensive wrapping.
* **Deliberative Planning:** Uses decision logic to maintain multi-step goals while preventing premature execution.
* **Short-Term Memory & State Management:** Ensures the session buffer accurately reflects order status without persisting unverified or corrupted states.
* **System Transparency & Resilience:** Gracefully degrades performance (human triage) rather than failing catastrophically, maintaining clear, traceable feedback loops for both end users and operators.