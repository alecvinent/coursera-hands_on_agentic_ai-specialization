How would you design guardrails for unpredictable input next time?

To protect an AI agent from unpredictable input, guardrails must be designed as a multi-layered defense system that validates input, constrains execution, and safely handles edge cases.

Input Classification & Sanitization

* Pre-Routing Classifier: Use a small, lightweight model or intent classifier upstream to intercept requests before they reach the main agent. Filter out prompt injections, out-of-scope requests, malicious payloads, or gibberish.
* Schema & Type Enforcement: Enforce strict type constraints and structural schemas on tool parameters to prevent malformed or invalid data from reaching APIs.

Execution Constraints & Flow Control

* Max Loop Limits & Budgeting: Set explicit execution limits (e.g., maximum 3 tool retries, strict token budgets, and execution timeouts) to prevent infinite loops when handling ambiguous or nonsensical instructions.
* Deterministic Decision Trees: Keep standard, critical workflows predictable by routing fixed procedures through code or deterministic state machines rather than relying purely on LLM reasoning for every step.

Output Validation & Graceful Fallbacks

* Schema Validation on Tool Calls: Validate the model's generated parameters against a predefined schema before executing a function. If validation fails, feed the specific schema error back to the model as a clear, structured system message instead of running the call.
* Safe Fallback States: Design defensive fallback logic for unexpected tool responses or unresolvable loops. Instead of returning raw technical errors or hallucinating answers, instruct the agent to clarify missing parameters with the user or exit gracefully to a human operator.