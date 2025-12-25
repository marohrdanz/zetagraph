from dotenv import load_dotenv
import log_setup
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from os import getenv

load_dotenv()
logger = log_setup.configure_logging()
model = getenv("ANTHROPIC_MODEL", "claude-2")

class AnalysisState(TypedDict):
    question: str
    needs_search: bool
    search_query: str
    answer: str

def analyze_question(state: AnalysisState) -> AnalysisState:
    """Determine if we need to search for information."""
    logger.debug(f"Analyzing question: {state['question']}")
    llm = ChatAnthropic(model=model, temperature=0)
    prompt = f"""Does this question require current infromation or web search? Question: {state['question']}. Respond ONLY with 'YES' or 'NO'."""
    response = llm.invoke([HumanMessage(content=prompt)])
    logger.debug(f"LLM response for checking if we need a search: {response.content}")
    state["needs_search"] = "YES" in response.content.upper()
    logger.debug(f"Question needs a web search: {state['needs_search']}")

    if state["needs_search"]:
        # Generate search query
        query_prompt = f"Generate a concise search query for: {state['question']}"
        query_response = llm.invoke([HumanMessage(content=query_prompt)])
        state["search_query"] = query_response.content

    return state

def search_node(state: AnalysisState) -> AnalysisState:
    """Simulate a web search."""
    ## to be relplaced with actual search logic
    state["answer"] = f"Search results for: {state['search_query']}"
    logger.debug("Faked a search operation.")
    return state

def direct_answer_node(state: AnalysisState) -> AnalysisState:
    """Answer the question directly (no web search)."""
    llm = ChatAnthropic(model=model, temperature=0)
    response = llm.invoke([HumanMessage(content=state["question"])])
    state["answer"] = response.content
    logger.debug(f"Direct answer: {state['answer']}")
    return state

def route_question(state: AnalysisState) -> Literal["search", "direct_answer"]:
    """Conditional routing based on whether or not a search is needed."""
    if state["needs_search"]:
        return "search"
    return "direct_answer"

# Build graph
workflow = StateGraph(AnalysisState)
workflow.add_node("analyze_question", analyze_question)
workflow.add_node("search", search_node)
workflow.add_node("direct_answer", direct_answer_node)
workflow.set_entry_point("analyze_question")
workflow.add_conditional_edges(
    "analyze_question",
    route_question,
    {
        "search": "search",
        "direct_answer": "direct_answer"
    }
)
workflow.add_edge("search", END)
workflow.add_edge("direct_answer", END)

app = workflow.compile()

# Testing direct answer path
result_direct = app.invoke({
                           "question": "What is 2-9?}",
                           "needs_search": False,
                           "search_query": "",
                           "answer": ""
})
print(f"Direct answer result: {result_direct['answer']}")


# Testing search path
result2 = app.invoke({
                     "question": "What's the latest news in space exploration?",
                     "needs_search": False,
                     "search_uqery": "",
                     "answer": ""
})
print(f"Search answer result: {result2['answer']}")
