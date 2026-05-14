import asyncio, pytest
from unittest.mock import AsyncMock, patch
from backend.orchestrator import Session, SessionState, PipelineStage

def test_session_state_defaults():
    state = SessionState()
    assert state.requirements is None
    assert state.bom is None
    assert state.stage == PipelineStage.REQUIREMENTS
    assert state.correction_attempts == 0

@pytest.mark.asyncio
async def test_session_user_input_queue():
    messages = []
    async def fake_send(msg): messages.append(msg)

    session = Session("test-id", fake_send)
    asyncio.get_event_loop().call_soon(lambda: asyncio.ensure_future(session.put_user_input("hello")))
    result = await session.wait_for_user_input()
    assert result == "hello"
