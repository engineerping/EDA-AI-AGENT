from typing import TypedDict

class AgentState(TypedDict, total=False):
    stage: str
    requirements: dict | None
    bom: list[dict] | None
    schematic_content: str | None
    erc_report: dict | None
    correction_attempts: int
    iteration_count: int
    messages: list[dict]
    design_context: str