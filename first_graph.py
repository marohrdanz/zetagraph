from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
import log_setup
from typing import TypedDict

load_dotenv()
logger = log_setup.configure_logging()

##
## This is the hello world of LangGraph
##

# State is a shared data structure passed between nodes
class State(TypedDict):
    """Define the structure of the state passed between nodes"""
    message: str
    response: str

# Define a greeter node
# Nodes are functions that perform work, e.g. call LLMs, search tools, etc.
def greeter_node(state: State) -> State:
    """Generate a greeting"""
    name = state["message"]
    state["response"] = f"Hello, {name}, or should I say, 'Hello World!'"
    return state

# Build the graph
workflow = StateGraph(State)
workflow.set_entry_point("greeter")
workflow.add_node("greeter", greeter_node)
# Edges are connections between the nodes that define the flow
workflow.add_edge("greeter", END)

# Compile and run
app = workflow.compile()
result = app.invoke({"message": "Alice", "resonse": ""})
print(result["response"])
logger.info("Final response: %s", result["response"])

mermaid_code = app.get_graph().draw_mermaid()
print("\nMermaid Diagram:\n")
print(mermaid_code)
