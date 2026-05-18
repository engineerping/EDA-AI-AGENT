from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from backend.orchestrator.langgraph_state import AgentState

def route_after_validation(state: AgentState) -> str:
    error_count = state.get("erc_report", {}).get("error_count", -1)
    if error_count > 0 and state.get("correction_attempts", 0) < 3:
        return "design_agent"
    return END


def build_orchestrator_graph():
    builder = StateGraph(AgentState)
    builder.add_node("req_agent", lambda s: s)
    builder.add_node("design_agent", lambda s: s)
    builder.add_node("gen_agent", lambda s: s)
    builder.add_node("validation_agent", lambda s: s)
    builder.add_edge(START, "req_agent")
    builder.add_edge("req_agent", "design_agent")
    builder.add_edge("design_agent", "gen_agent")
    builder.add_edge("gen_agent", "validation_agent")
    builder.add_conditional_edges("validation_agent", route_after_validation)
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)