from typing import Optional, List, Dict
from pydantic import BaseModel

class TravelAgentState(BaseModel):
    destination: Optional[str] = None
    hotel_options: List[str] = []
    selected_hotel: Optional[str] = None
    step: str = "INIT"  # States: INIT, AWAITING_HOTEL_SELECTION, CONFIRMING, BOOKED

def process_turn(state: TravelAgentState, user_input: str) -> Dict[str, str]:
    # 1. Global Intent Intercept (Handles mid-stream changes)
    if "change destination" in user_input.lower() or "go somewhere else" in user_input.lower():
        state.destination = None
        state.selected_hotel = None
        state.hotel_options = []
        state.step = "INIT"
        return {"response": "Where would you like to travel instead?", "state": state}

    # 2. State-Based Execution Branching
    if state.step == "INIT" or not state.destination:
        state.destination = extract_destination(user_input)
        state.hotel_options = fetch_hotels(state.destination)
        state.step = "AWAITING_HOTEL_SELECTION"
        return {
            "response": f"Here are 3 options for {state.destination}: {state.hotel_options}. Which one do you prefer?",
            "state": state
        }

    elif state.step == "AWAITING_HOTEL_SELECTION":
        # Resolve ordinal choices ("second one", "option 2") or named choices
        selected = parse_ordinal_or_name(user_input, state.hotel_options)
        if selected:
            state.selected_hotel = selected
            state.step = "CONFIRMING"
            return {
                "response": f"You've chosen {state.selected_hotel} in {state.destination}. Shall I proceed with booking?",
                "state": state
            }
        else:
            # Explicit fallback without state wipe
            return {
                "response": "I didn't catch that choice. Please specify option 1, 2, or 3, or state the hotel name.",
                "state": state
            }

    return {"response": "Sorry, I encountered an unexpected step.", "state": state}