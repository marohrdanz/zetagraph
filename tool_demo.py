from dotenv import load_dotenv
import log_setup
from langchain_ollama import ChatOllama
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from os import getenv
import sys
import json

## This is a quick-and-dirty demo of LangGraph
## with some branching

load_dotenv()
logger = log_setup.configure_logging()
model = getenv("MODEL")
if model is None:
    logger.error("Missing required env: MODEL")
    sys.exit(1)

llm = ChatOllama(model=model, temperature=0)

class ToolState(TypedDict):
    question: str
    tool_choice: Literal["calculator", "search", "weather"]
    answer: str

def analyze_and_route(state: ToolState) -> ToolState:
    """LLM determines which tool is needed"""
    prompt = f"""Analyze this user query and decide which tool is best to answser their question:

Query: {state['question']}

Choose ONE of these tools:
- calculator: For math problems, arithmetic, calculations
- weather: For weather questions (e.g., "What's the weather in X?", "Is it raining?")
- search: For current events, general facts, "who/what/when" questions

Response ONLY with the tool name (no puncutation or explanation.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    state['tool_choice'] = response.content.lower()
    return state

def route_to_tool(state: ToolState) -> str:
    return state['tool_choice']
    
def run_calculator(state: ToolState) -> ToolState:
    prompt =f"""Convert this text into a mathematical expression for use by python:

{state['question']}

Respond only with the expression. Do not include other text.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    state['answer'] = f"""The answer to {response.content} is {eval(response.content)}"""
    return state

def run_weather(state: ToolState) -> str:
    """Fake a weather service"""
    prompt = f"""You are a weather service.

A user searched for: "{state['question']}"

Provide a brief, realistic estimate of how the weather might be today.
Do NOT say you're an AI or that you don't know what the weather is.
Just give a plausible answer as if you were a weather service.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    state['answer'] = response.content
    return state

def run_search(state: ToolState) -> str:
    """Fake web search"""
    prompt = f"""You are a search engine. A user searched for:

"{state['question']}"

Provide a brief, realistic search result (2-3 sentences).
Do NOT say you're an AI or that you can't search.
Just give a plausible answer as if you found it on the web.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    state['answer'] = response.content
    return state

workflow = StateGraph(ToolState)
workflow.add_node("analyze_and_route", analyze_and_route)
workflow.add_node("calculator", run_calculator)
workflow.add_node("weather", run_weather)
workflow.add_node("search", run_search)
workflow.set_entry_point("analyze_and_route")
workflow.add_edge(START, "analyze_and_route")
workflow.add_edge("analyze_and_route", END)
workflow.add_conditional_edges(
    "analyze_and_route",
    route_to_tool,
    {
        "calculator": "calculator",
        "weather": "weather",
        "search": "search"
    }
)

app = workflow.compile()

result = app.invoke({
        "question": "What are the main movements in CrossFit?",
        "tool_choice": "",
        "answer": ""
    })

print(json.dumps(result, indent=2))
