### Question 1: What did you find most difficult while debugging the agent?

The most difficult part of debugging the agent was rewriting flows without overfitting to specific failures.

While execution logs make it relatively straightforward to trace where a tool call failed or where a logic breakdown occurred, designing a generalizable fix without making the system rigid is much more complex.

* The Overfitting Trap: Patching a failure by adding narrow instructions (e.g., *"If the user asks for information about X, never call search_tool"*) easily resolves that exact log run. However, these band-aid rules create regressions elsewhere—limiting the agent's ability to handle valid edge cases and cluttering the system prompt with fragile, hyper-specific logic.


* Concrete Example from Debugging: During one of the agent runs, when the agent entered an infinite retry loop after receiving an unhelpful tool response, the quick temptation was to hardcode a rule targeting that exact tool output. The true difficulty was stepping back to rewrite the agent's step-by-step evaluation framework so it could detect *any* repetitive, unhelpful response and adjust its tactic generally.


* Generalization vs. Control: Finding the right abstraction level requires shifting from hardcoded scripts to structural prompt constraints. The core challenge lies in guiding the agent's overall reasoning process so the fix holds across diverse, unseen user inputs while preserving model flexibility.