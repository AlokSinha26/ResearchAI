# app/agent.py
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from typing import Annotated, TypedDict
from app.tools import web_search, read_pdf, query_memory
from app.schemas import ResearchOutput

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

tools = [web_search, read_pdf, query_memory]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0
).bind_tools(tools)

structured_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0
).with_structured_output(ResearchOutput)


def call_model(state: AgentState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "end"


tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")

app_graph = graph.compile()


def run_research(query: str) -> ResearchOutput:
    """Run the full agent loop, then convert the result into structured output."""
    result = app_graph.invoke({"messages": [("user", query)]})

    finalize_prompt = (
        "Based on the conversation above, produce a ResearchOutput summary. "
        "List every distinct source you used (web search results, PDFs read, or memory lookups) "
        "with a short summary of what each contributed, then give your overall synthesis and confidence level. "
        "Do not include the query field — it will be set separately."
    )

    structured_result = structured_llm.invoke(
        result["messages"] + [("user", finalize_prompt)]
    )

    # Overwrite query with the original question, rather than trusting the model
    # to correctly identify it from conversation history (it sometimes picks up
    # the finalize instruction itself instead).
    structured_result.query = query

    return structured_result