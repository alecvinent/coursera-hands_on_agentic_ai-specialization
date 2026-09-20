**Capstone Project Overview & Blueprint**

**Agent Overview**
The **Smart Order & Support Agent (SOSA)** addresses the operational friction independent cafeterias and bistros face when managing multi-channel digital orders and customer support queries simultaneously. Built for small business owners and busy service staff, SOSA acts as an autonomous digital concierge. It receives incoming customer messages, parses structured ordering intent, verifies inventory and operating parameters, and formats structured order confirmations or support resolutions.

SOSA operates by combining natural language processing with tool orchestration. Upon receiving an inbound request, it parses the payload, updates short-term conversational memory, queries an inventory API, and routes the validated result via external webhooks (such as WhatsApp). By automating routine intake and triage, the agent minimizes manual data entry errors, reduces order drop-off rates, and ensures continuous service during peak operational hours.

---

**Architecture Design**

* **Agent Paradigm:** **Hybrid Architecture** — Combining reactive rule-based routing for direct tool triggers with a deliberative LLM planner for multi-step fallback handling and dynamic intent resolution.
* **Core Modules:**
* **Perception:** Text input parser and payload normalizer for extracting customer intent, items, quantities, and contact preferences.
* **Planning:** Dynamic task coordinator utilizing step-by-step decision logic (Intent Classification $\rightarrow$ Inventory Check $\rightarrow$ Draft Order $\rightarrow$ External Dispatch).
* **Tools:** Inventory/Catalog Database API, Pricing Engine, and WhatsApp/Messaging Webhook Integration.
* **Memory:** Short-term session buffer (storing ongoing order state and user context across conversational turns).
* **Fallback & Recovery:** Exception handler that intercepts API downtime, out-of-stock items, or ambiguous customer inputs, triggering human escalation or self-correction loops.



---

**Code / Logic Excerpt**

```python
# Planner and Error Recovery Logic Snippet
from typing import Dict, Any

class OrderPlannerAgent:
    def __init__(self, inventory_tool, messaging_tool, memory_store):
        self.inventory = inventory_tool
        self.messaging = messaging_tool
        self.memory = memory_store

    def process_request(self, session_id: str, user_input: str) -> Dict[str, Any]:
        # 1. Retrieve session context / memory
        history = self.memory.get_context(session_id)
        
        # 2. Parse intent and items (Deliberative step)
        parsed_intent = self.parse_intent(user_input, history)
        
        if parsed_intent.get("type") == "AMBIGUOUS":
            return self.messaging.send_clarification(
                session_id, "Could you specify which item size or preference you would like?"
            )

        # 3. Tool Orchestration with Fallback Case Handling
        order_items = parsed_intent.get("items", [])
        unavailable_items = []
        
        for item in order_items:
            try:
                stock_status = self.inventory.check_stock(item["id"])
                if not stock_status["available"]:
                    unavailable_items.append(item["name"])
            except Exception as api_error:
                # Tool error recovery: Fall back to human escalation
                return self.handle_fallback(session_id, f"Inventory API connection failed: {api_error}")

        # 4. Execute decision logic based on tool checks
        if unavailable_items:
            # Self-correction / Alternative path
            self.memory.update_context(session_id, {"pending_substitutions": unavailable_items})
            return {
                "status": "RETRY_NEEDED",
                "message": f"Sorry, the following items are currently out of stock: {', '.join(unavailable_items)}. Would you like to substitute them?"
            }

        # 5. Finalize order and update memory
        confirmed_order = self.inventory.reserve_items(order_items)
        self.memory.update_context(session_id, {"order_status": "CONFIRMED", "order_id": confirmed_order["id"]})
        
        return self.messaging.send_whatsapp_payload(session_id, confirmed_order)

    def handle_fallback(self, session_id: str, error_msg: str) -> Dict[str, Any]:
        # Route directly to human agent triage
        return {
            "status": "ESCALATED",
            "message": "I've flagged your request for a staff member to complete manually. Thank you for your patience!",
            "internal_log": error_msg
        }

```

---

**Behavior Trace & Walkthrough**

* **Scenario 1: Standard Interaction Flow**
* **User Input:** "Hi, I'd like to order 2 Espressos and 1 Croissant for pickup."
* **Perception/Planning:** Parses intent as `CREATE_ORDER`; items extracted: `[{"item": "Espresso", "qty": 2}, {"item": "Croissant", "qty": 1}]`.
* **Tool Execution:** Calls `inventory.check_stock()` for Espresso and Croissant $\rightarrow$ Returns `Available`.
* **Decision & Memory:** Formats order payload, stores pending order state in short-term memory, and calls `messaging.send_whatsapp_payload()`.
* **Result:** Customer receives formatted order confirmation message on WhatsApp with order total and pickup estimated time.


* **Scenario 2: Failure & Edge Case Handling (Out-of-Stock / Ambiguity)**
* **User Input:** "Can I get a cappuccino and whatever pastry is fresh?"
* **Perception/Planning:** Identifies ambiguous item ("whatever pastry is fresh") and checks stock for "cappuccino".
* **Tool Execution:** `inventory.check_stock("cappuccino")` fails due to coffee bean inventory depletion.
* **Fallback Execution:** The system catches the out-of-stock signal and ambiguity simultaneously, triggering the fallback loop instead of crashing or generating a hallucinatory order.
* **Result:** Agent prompts: *"Our cappuccino is temporarily out of stock today! We have Americanos and Flat Whites available. For pastries, we have fresh Croissants and Scones—which would you prefer?"*



---

**Reflection**

* **Most Proud Design Decision:** Implementing an explicit fallback interception layer before sending payload updates to external APIs. This prevents partial state changes or corrupt orders from reaching the WhatsApp webhook when external tools error out.
* **Hardest Part to Get Right:** Balancing natural language extraction flexibility with strict operational schema validation so ambiguous customer queries are gracefully clarified rather than incorrectly processed.
* **Future Iteration Improvements:** Incorporate persistent cross-session memory (via a database vector store) to recall past customer preferences, enabling personalized recommendations and faster re-ordering workflows.