import pytest, json
from backend.orchestrator.orchestrator_module import Session, Orchestrator, PipelineStage, SessionState

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline_stm32_robot():
    """Send circuit requirements for STM32 robot controller.
    Verify: requirements parsed + BOM generated + schematic content exists."""

    messages_sent = []
    async def fake_send(msg: dict):
        messages_sent.append(msg)

    session = Session(session_id="test-001", send=fake_send)

    # Pre-seed requirements as if ReqAgent had already finalized them
    # (avoids multi-turn dialog in test — downstream pipeline is what we're testing)
    session.state.requirements = {
        "function": "robot controller",
        "input_voltage": "5V USB or 7-12V LiPo",
        "output_voltage": "3.3V",
        "output_current_ma": 500,
        "form_factor": "robot chassis",
        "cost_tier": "hobbyist",
        "notes": "STM32F4, 4 motor drivers"
    }

    orchestrator = Orchestrator(session=session)

    await orchestrator.run("I need an STM32F4 robot controller board with 4 motor drivers")

    # Verify pipeline completed
    assert session.state.stage == PipelineStage.DONE, f"Expected DONE, got {session.state.stage}"
    assert session.state.iteration_count > 0

    # Verify BOM was generated
    assert session.state.bom is not None, "BOM should not be None"
    assert len(session.state.bom) > 0, f"BOM should not be empty: {session.state.bom}"

    # Verify schematic content exists (non-empty S-expression)
    assert session.state.schematic_content, "schematic_content should not be empty"
    assert "(kicad_sch" in session.state.schematic_content, "Should be valid KiCad S-expression"