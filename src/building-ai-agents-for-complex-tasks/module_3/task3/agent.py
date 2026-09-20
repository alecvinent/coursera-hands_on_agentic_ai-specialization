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