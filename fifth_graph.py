from dotenv import load_dotenv
import textwrap
import json
import log_setup
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from os import getenv
from ddgs import DDGS
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
import sys

load_dotenv()
logger = log_setup.configure_logging()
model = getenv("MODEL")
if model is None:
    logger.error("Missing required env: MODEL")
    sys.exit(1)
memory = MemorySaver()

class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    research_plan: str
    search_results: list
    draft_answer: str
    final_answer: str
    iteration: int
    max_iterations: int
    is_approved: bool
    reviewer_comments: str

def planner_node(state: ResearchState) -> ResearchState:
    """Create research plan"""
    llm = ChatOllama(model=model, temperature=0.7)
    prompt = f"""Create a research plan to answer this question: {state['question']}.
        List 2-3 specific search queries that would help answer this question comprehensively.
        Format as a numbered list."""
    response = llm.invoke([HumanMessage(content=prompt)])
    state['research_plan'] = response.content
    state['iteration'] = 0
    state['max_iterations'] = 3
    state['is_approved'] = False
    logger.debug(f"Research plan:\n\n{textwrap.indent(state['research_plan'], '     ')}")
    return state

def researcher_node(state: ResearchState) -> ResearchState:
    """Execute seraches based on the research plan."""
    search = DuckDuckGoSearchRun()
    # Extract queries from plan (simplified parsing)
    lines = state['research_plan'].split('\n')
    queries = [line.split('.', 1)[-1].strip() for line in lines if line.strip() and line[0].isdigit()]
    results = []
    for query in queries[:3]: # just look at first 3 queries
        try:
            result = search.run(query)
            results.append(f"Query: {query}\nResults: {result}\n")
            logger.debug(f"Search results for '{query}'\n\n{textwrap.indent(result, '     ')}")
        except Exception as e:
            logger.error(f"Search.run failed for {query}: {e}")
            results.append(f"Query: {query}\nResults: no results found.\n")
    state['search_results'] = results
    return state

def writer_node(state: ResearchState) -> ResearchState:
    """Write answer based on research."""
    llm = ChatOllama(model=model, temperature=0)
    research_context = "\n\n".join(state['search_results'])
    feedback_context = ""
    if state.get('reviewer_comments'):
        feedback_context = f"""
            IMPORTANT - Previous feedback to address:
            {state['reviewer_comments']}
            Previous draft (needs improvement):
            {state['draft_answer']}
         """
        logger.warning(f"Incorporating reviewer feedback:\n\n{textwrap.indent(feedback_context, '     ')}")
    prompt = f"""Based on the following research, write a comprehensive answer to the question.
              Question: {state['question']}
              Research: {research_context}
                        {feedback_context}
              Provide a clear, well structured answer, and write your response as if you were slashdot commenter."""
    logger.debug(f"Writer prompt:\n\n{textwrap.indent(prompt, '     ')}")
    response = llm.invoke([HumanMessage(content=prompt)])
    state['draft_answer'] = response.content
    state['iteration'] += 1
    return state

def reviewer_node(state: ResearchState) -> ResearchState:
    """Review and finalize the answer."""
    llm = ChatOllama(model=model, temperature=0)
    prompt = f"""Review this answer for accuracy and completelness:
              Question: {state['question']}
              Asnwer: {state['draft_answer']}
              Evaluate this answer for clarity, and ensure it's written in the style of slashdot commenter.
              Respond in this format:
              DECISION: [APPROVED or NEEDS_REVISION]
              COMMENTS: [If needs revision, explain what specific improvements are needed. If approved, leave blank.]"""
    response = llm.invoke([HumanMessage(content=prompt)])
    
    if "APPROVED" in response.content.upper() and "NEEDS_REVISION" not in response.content.upper():
        logger.info(f"Answer approved by AI. Comments from AI:\n\n{textwrap.indent(response.content, '     ')}")
        state['final_answer'] = state['draft_answer']
        state['is_approved'] = True
        state['reviewer_comments'] = ""
    else:
        logger.warning(f"Answer not approved by AI. Comments from AI:\n\n{textwrap.indent(response.content, '     ')}")
        state['is_approved'] = False
        if "COMMENTS:" in response.content:
            comments = response.content.split("COMMENTS:", 1)[-1].strip()
            state['reviewer_comments'] = comments
        else:
            logger.warning("No COMMENTS found in reviewer response; adding default comment.")
            state['reviewer_comments'] = "No specific comments provided."
        state['final_answer'] = state['draft_answer'] + "\n\n[Note: Answer may need refinement]"
    return state

def human_approval_node(state: ResearchState) -> ResearchState:
    """Wait for human approva."""
    print(f"\nHere is the current draft answer:\n\n{textwrap.indent(state['draft_answer'], '     ')}\n\n")
    aproval = input("Do you approve this answer? (y/n): ")

    if aproval.lower() == 'y':
        state['final_answer'] = state['draft_answer']
        state['is_approved'] = True
    else:
        feedback_context = input("What should be improved? (Type feedback, or leave blank to use AI review comments): ")
        if feedback_context.strip() == "":
            feedback_context = state.get('reviewer_comments', 'No specific comments provided.')
        state['reviewer_comments'] = feedback_context
        state['is_approved'] = False
    return state

def should_continue(state: ResearchState) -> Literal["writer", "end"]:
    """Decide if we need another iteration."""
    logger.debug(f"Deciding if we should continue. Current iteration: {state['iteration']}. Approved: {state['is_approved']}")
    if state['is_approved']:
        return 'end'
    if state['iteration'] >= state['max_iterations']:
        state['final_answer'] = state['draft_answer'] + "\n\n[Note: Answer may need refinement]"
        return 'end'
    return 'writer'

# Build the graph
workflow = StateGraph(ResearchState)
workflow.add_node('planner', planner_node)
workflow.add_node('researcher', researcher_node)
workflow.add_node('writer', writer_node)
workflow.add_node('reviewer', reviewer_node)
workflow.add_node('human_approval', human_approval_node)

workflow.set_entry_point('planner')
workflow.add_edge('planner', 'researcher')
workflow.add_edge('researcher', 'writer')
workflow.add_edge('writer','reviewer')
workflow.add_edge('reviewer', 'human_approval')
workflow.add_conditional_edges(
    'human_approval',
    should_continue,
    {
        'writer': 'writer',
        'end': END
    }
)

app = workflow.compile()

result = app.invoke({
                    "messages": [],
                    "question": "What are the benefits of deadlifts and squats for building overall strength?",
                    "research_plan": "",
                    "search_results": [],
                    "draft_answer": "",
                    "final_answer": "",
                    "reviewer_comments": "",
                    "iteration": 0,
                    "max_iterations": 10,
                    "is_approved": False,
})
logger.debug(json.dumps(result, indent=2))
print(f"\nFinal Answer:\n{result['final_answer']}\n")

mermaid_code = app.get_graph().draw_mermaid()
print("\nMermaid Diagram:\n")
print(mermaid_code)
