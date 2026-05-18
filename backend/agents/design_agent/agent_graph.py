from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from typing import TypedDict

from backend.mcp.tools.compdb import compdb_search, compdb_add


class DesignAgentState(TypedDict, total=False):
    messages: list[dict]
    bom: list[dict] | None
    design_context: str | None


def build_design_agent_graph():
    builder = StateGraph(DesignAgentState)
    # Wire compdb_search and compdb_add as MCP tools via ToolNode
    design_tools = [compdb_search, compdb_add]
    builder.add_node("design_tools", ToolNode(design_tools))
    builder.add_edge(START, "design_tools")
    builder.add_edge("design_tools", END)
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)