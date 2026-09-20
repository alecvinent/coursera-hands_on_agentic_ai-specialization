This lab assignment focuses on diagnosing AI agent failures using interaction logs and fixing them through prompt engineering or workflow adjustments.

Based on the instructions provided in the PDF, here is a structured template and guide you can use to complete the analysis for both agent runs:

---

### **Agent Run 1 Analysis**

**1. Visible Failure**

* **Issue:** [e.g., *Tool Misuse / Infinite Looping / Hallucination / Unhandled Fallback*]
* **Description:** [Describe what the agent did incorrectly during the interaction log.]

**2. Likely Root Cause**

* **Diagnosis:** [e.g., *Vague instructions in system prompt, lack of explicit tool parameters, missing stop conditions, or weak error handling logic.*]

**3. Proposed Fix & Explanation**

* **Updated Prompt / Flow:**
> **Revised System Instructions:**
> *"You are an AI assistant. [Insert updated explicit constraints, step-by-step logic, edge-case fallback rules, and explicit tool guidelines here]."*


* **Why it improves performance:** [Briefly explain how the additions prevent the failure observed above.]

---

### **Agent Run 2 Analysis**

**1. Visible Failure**

* **Issue:** [e.g., *Tool Misuse / Infinite Looping / Hallucination / Unhandled Fallback*]
* **Description:** [Describe what the agent did incorrectly during the interaction log.]

**2. Likely Root Cause**

* **Diagnosis:** [e.g., *Ambiguous user context, missing retrieval validation, lack of step-by-step verification before calling an API.*]

**3. Proposed Fix & Explanation**

* **Updated Prompt / Flow:**
> **Revised System Instructions:**
> *"You are an AI assistant. [Insert updated explicit constraints, step-by-step logic, edge-case fallback rules, and explicit tool guidelines here]."*


* **Why it improves performance:** [Briefly explain how the additions prevent the failure observed above.]

---

### Common Failure Patterns to Look For in Your Logs

* **Tool Misuse:** Calling the wrong API, passing incorrect argument types, or invoking a tool when direct reasoning or standard response is sufficient.
* **Agent Looping:** Re-running the same failed tool call repeatedly without updating inputs or changing tactics.
* **Hallucination:** Generating factual statements or parameters not grounded in tool outputs or provided context.
* **Fallback Failure:** Crashing or returning raw technical errors directly to the user when a tool call fails.
