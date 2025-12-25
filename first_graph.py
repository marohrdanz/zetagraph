from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
import log_setup
from typing import TypedDict

load_dotenv()
logger = log_setup.configure_logging()

# Defin the state structure
class State(TypedDict):
    message: str
    response: str

# Define node functions
def greeter_node(state: State) -> State:
    """Generate a greeting"""
    name = state["message"]
    state["response"] = f"Hello, {name}! Welcome to LangGraph."
    return state

# Build the graph
workflow = StateGraph(State)
workflow.add_node("greeter", greeter_node)
workflow.set_entry_point("greeter")
workflow.add_edge("greeter", END)

# Compile and run
app = workflow.compile()
result = app.invoke({"message": "Alice", "resonse": ""})
print(result["response"])
logger.info("Final response: %s", result["response"])
