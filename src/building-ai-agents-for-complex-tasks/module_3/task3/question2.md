**Q2: What was the hardest part to get right?**

The hardest part of this capstone to engineer and fine-tune was **balancing natural language extraction flexibility with strict operational schema validation**.

### The Underlying Challenge & UX/System Impact

In real-world ordering scenarios, human language is inherently non-deterministic, elliptical, and full of implied intent. Customers frequently send vague or open-ended inputs—such as *"Get me a cappucino and whatever pastry is fresh"* or *"I'll take the usual."*

From a system architecture perspective, this creates a severe tension:

* **The Flexibility Goal:** Allowing users to communicate in natural, conversational phrases without forcing them to navigate rigid, robotic menu options.
* **The Operational Reliability Goal:** Requiring 100% deterministic, strongly-typed JSON schemas (e.g., specific `sku_id`, exact `quantity`, required `options/size`) before dispatching payloads to database APIs or WhatsApp webhooks.

If the agent leans too far toward loose extraction, it risks **hallucination and payload corruption**—such as assigning an arbitrary default item price, generating non-existent SKUs, or committing an incomplete order to the database. Conversely, if it leans too far toward rigid validation, it creates **friction and user frustration** by rejecting minor phrasing variations or demanding repetitive confirmations for self-evident requests.

### Engineering Solution: Multi-Layered Schema Validation & Dynamic Clarification

To bridge this gap, I developed a three-stage validation pipeline combining prompt constraints, structural output parsing, and deterministic guardrails:

```
[ Unstructured Input ] 
       │
       ▼
 1. System Prompt (Constraint-Enforced Extraction)
       │
       ▼
 2. Dynamic Pydantic / Schema Validation Layer
       │
       ├─── Status: VALID ─────────► [ Execute Inventory Tool ]
       │
       └─── Status: AMBIGUOUS ─────► [ Trigger Targeted Clarification Loop ]

```

#### 1. System Prompt Strategy (Strict Boundary Extraction)

Rather than asking the LLM to complete missing information, the extraction prompt explicitly forces the LLM to categorize unconfirmed properties as `null` or `AMBIGUOUS_REQ` rather than guessing:

```yaml
# Extraction System Prompt Excerpt
System: You are an order parsing engine. Extract items from user input into JSON.
CRITICAL RULE: Never guess, assume, or infer missing attributes (e.g., sizes, pastry types, flavors).
If an item is referenced generically (e.g., "fresh pastry", "a coffee"), set:
{
  "item_name": "UNKNOWN",
  "raw_reference": "<exact user string>",
  "requires_clarification": true,
  "missing_field": "item_selection"
}

```

#### 2. Deterministic Validation & Clarification Loops

When the JSON parser detects `requires_clarification: true` or a failed schema field, the deliberative planner intercepts the flow **before** calling the inventory API. Instead of halting or failing, it dynamically constructs a targeted clarification prompt containing known menu alternatives:

```python
# Clarification Orchestration Snippet
if parsed_output.requires_clarification:
    # Query database for available items matching the raw category
    available_pastries = inventory_db.get_available_category("pastries")
    
    # Prompt user with specific, helpful options instead of generic errors
    return messaging.send_message(
        f"We have fresh {', '.join(available_pastries)} today! Which one would you like with your cappuccino?"
    )

```

### Iterative Failures & Trade-Offs

During testing, initial iterations suffered from two key failure modes:

1. **Over-Clarification Loops:** Asking users to confirm implicit defaults (e.g., asking "Do you want 1 cappuccino?" when the user said "Can I get a cappuccino?"). I resolved this by establishing explicit defaults in the schema for standard quantities while strictly requiring user input for distinct SKUs.
2. **Cascading Ambiguity:** When users responded to a clarification with another open-ended request (e.g., Agent: *"Which pastry?"* $\rightarrow$ User: *"Surprise me!"*). To handle this without infinite loops, I set a threshold: after **2 unsuccessful clarification attempts**, the agent gracefully falls back to human operator triage.

### Lessons & Impact on Future Agent Designs

This challenge fundamentally shaped how I approach agent engineering:

* **LLMs for Intent, Deterministic Code for Enforcements:** Rely on LLMs strictly for intent classification and text parsing, but shift all business logic, schema validation, and state progression into explicit, deterministic code wrappers.
* **Designing for Failure Modes First:** Moving forward, I prioritize defining `AMBIGUOUS` and `UNKNOWN` states in the initial architecture data models, rather than treating them as edge-case exceptions handled after the fact.