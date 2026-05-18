from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict


class ReqAgentState(TypedDict, total=False):
    messages: list[dict]
    pending_questions: list[str]
    collected_spec: dict | None


def build_req_agent_graph():
    builder = StateGraph(ReqAgentState)
    builder.add_node("ask_question", lambda s: s)
    builder.add_node("finalize", lambda s: s)
    builder.add_edge(START, "ask_question")
    builder.add_edge("ask_question", "finalize")
    builder.add_edge("finalize", END)
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)