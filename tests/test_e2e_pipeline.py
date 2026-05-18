import pytest, json
from backend.orchestrator.orchestrator_module import Session, Orchestrator, PipelineStage, SessionState

@pytest.mark.asyncio
async def test_full_pipeline_stm32_robot():
    """Send circuit requirements for STM32 robot controller.
    Verify: requirements parsed + BOM generated + schematic content exists."""

    messages_sent = []
    async def fake_send(msg: dict):
        messages_sent.append(msg)

    session = Session(session_id="test-001", send=fake_send)
    orchestrator = Orchestrator(session=session)

    # Run the orchestrator (synchronous wrapper for test)
    await orchestrator.run("I need an STM32F4 robot controller board with 4 motor drivers")

    # Verify pipeline completed
    assert session.state.stage == PipelineStage.DONE
    assert session.state.iteration_count > 0

    # Verify requirements were captured
    assert session.state.requirements is not None

    # Verify BOM was generated
    assert session.state.bom is not None
    assert len(session.state.bom) > 0

    # Verify schematic content exists (non-empty S-expression)
    assert session.state.schematic_content
    assert "(kicad_sch" in session.state.schematic_content