import pytest
from backend.orchestrator.langgraph_state import AgentState

def test_agent_state_fields():
    state = AgentState(
        stage="requirements",
        requirements={"function": "robot controller"},
        bom=[],
        schematic_content="",
        erc_report={"error_count": 0},
        correction_attempts=0,
        iteration_count=0,
        messages=[],
        design_context="",
    )
    assert state["stage"] == "requirements"
    assert state["correction_attempts"] == 0
    assert state["iteration_count"] == 0