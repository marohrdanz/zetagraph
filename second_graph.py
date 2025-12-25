from dotenv import load_dotenv
import log_setup
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict
from langgraph.graph import StateGraph, END

load_dotenv()
logger = log_setup.configure_logging()

class ChatState(TypedDict):
    messages: list
    question: str
    answer: str

def llm_node(state: ChatState) -> ChatState:
    """Call the LLM to answer a question"""
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

    messages = [
        SystemMessage(content="You are a sea pirate."),
        HumanMessage(content=state["question"])
    ]

    response = llm.invoke(messages)
    state["answer"] = response.content
    return state


# Build graph
workflow = StateGraph(ChatState)
workflow.add_node("llm", llm_node)
workflow.set_entry_point("llm")
workflow.add_edge("llm", END)

app = workflow.compile()
result = app.invoke({
                    "messages": [],
                    "question": "Where can I find buried treasure?",
                    "answer": ""
                     })
print(result["answer"])
logger.info("Final answer: %s", result["answer"])
