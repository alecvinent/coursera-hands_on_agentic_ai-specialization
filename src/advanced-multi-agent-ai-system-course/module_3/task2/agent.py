import os
import json
from typing import Dict, List, TypedDict, Literal, Annotated
from dataclasses import dataclass

# ==========================================
# 1. STATE DEFINITION & GOVERNANCE SCHEMAS
# ==========================================

class SystemState(TypedDict):
    task: str
    proposed_menu: List[Dict]
    purchase_orders: List[Dict]
    compliance_passed: bool
    budget_approved: bool
    requires_human_approval: bool
    arbitration_notes: List[str]
    agent_logs: List[str]

# ==========================================
# 2. AGENT DEFINITIONS & TOOL FUNCTIONS
# ==========================================

def kitchen_agent(state: SystemState) -> Dict:
    """Agent responsible for recipe planning and inventory needs."""
    task = state["task"]
    logs = state.get("agent_logs", [])
    logs.append("[Kitchen Agent]: Formulating daily special menu based on inventory.")
    
    # Proposed dish and required ingredients
    menu = [
        {"dish": "Pan-Seared Hake with Seafood Cream", "cost": 12.50, "temp_requirement": "cold_storage"},
        {"dish": "Artisanal Vegetable Risotto", "cost": 8.00, "temp_requirement": "dry_storage"}
    ]
    return {"proposed_menu": menu, "agent_logs": logs}


def compliance_agent(state: SystemState) -> Dict:
    """Agent responsible for safety checks and regulatory compliance."""
    menu = state.get("proposed_menu", [])
    logs = state.get("agent_logs", [])
    logs.append("[Compliance Agent]: Auditing food handling and storage compliance.")
    
    compliance_ok = True
    notes = []
    
    for item in menu:
        if item.get("temp_requirement") == "cold_storage":
            notes.append(f"VERIFIED: Cold storage chain validated for {item['dish']}.")
            
    return {
        "compliance_passed": compliance_ok, 
        "arbitration_notes": state.get("arbitration_notes", []) + notes,
        "agent_logs": logs
    }


def finance_agent(state: SystemState) -> Dict:
    """Agent responsible for margin calculation and purchase approval."""
    menu = state.get("proposed_menu", [])
    logs = state.get("agent_logs", [])
    logs.append("[Finance Agent]: Evaluating financial feasibility and draft purchase orders.")
    
    orders = [
        {"vendor": "Oceanic Fresh Ltd", "item": "Hake Fillets 10kg", "amount": 620.00},
        {"vendor": "Local Organics Co", "item": "Arborio Rice & Vegetables", "amount": 150.00}
    ]
    
    total_spend = sum(order["amount"] for order in orders)
    logs.append(f"[Finance Agent]: Total purchase order calculated: ${total_spend:.2f}")
    
    # Governance Guardrail: Purchases > $500 require Human-In-The-Loop (HITL)
    requires_hitl = total_spend > 500.00
    
    return {
        "purchase_orders": orders,
        "budget_approved": not requires_hitl,
        "requires_human_approval": requires_hitl,
        "agent_logs": logs
    }


def supervisor_agent(state: SystemState) -> Dict:
    """Orchestrator and Arbitrator regulating agent actions."""
    logs = state.get("agent_logs", [])
    logs.append("[Supervisor]: Reviewing state, resolving conflicts, and verifying safety bounds.")
    
    notes = state.get("arbitration_notes", [])
    
    if not state.get("compliance_passed", False):
        notes.append("ARBITRATION: Menu rejected due to safety compliance failure.")
        return {"arbitration_notes": notes, "agent_logs": logs}
        
    if state.get("requires_human_approval", False):
        notes.append("GOVERNANCE TRIGGER: Purchase limit ($500) exceeded. Escalating to Human-in-the-Loop.")
        
    return {"arbitration_notes": notes, "agent_logs": logs}

# ==========================================
# 3. WORKFLOW ENGINE / SIMULATOR EXECUTION
# ==========================================

class WorkflowEngine:
    def __init__(self):
        pass
        
    def run(self, initial_task: str):
        state: SystemState = {
            "task": initial_task,
            "proposed_menu": [],
            "purchase_orders": [],
            "compliance_passed": False,
            "budget_approved": False,
            "requires_human_approval": False,
            "arbitration_notes": [],
            "agent_logs": []
        }
        
        # Step 1: Kitchen Planning
        state.update(kitchen_agent(state))
        
        # Step 2: Compliance Verification
        state.update(compliance_agent(state))
        
        # Step 3: Financial & Sourcing Evaluation
        state.update(finance_agent(state))
        
        # Step 4: Supervisor Arbitration & Guardrail Enforcement
        state.update(supervisor_agent(state))
        
        return state

# Demonstration of execution
if __name__ == "__main__":
    engine = WorkflowEngine()
    result = engine.run("Optimize lunch menu and issue purchasing orders for tomorrow.")
    
    print("\n--- AGENT EXECUTION LOGS ---")
    for log in result["agent_logs"]:
        print(log)
        
    print("\n--- GOVERNANCE & ARBITRATION SUMMARY ---")
    for note in result["arbitration_notes"]:
        print(f"* {note}")
        
    print(f"\nRequires Human Approval: {result['requires_human_approval']}")