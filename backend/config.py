from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel

CONFIG_PATH = Path.home() / ".eda-agent" / "config.json"


class AgentConfig(BaseModel):
    model: str = "anthropic/claude-opus-4-7"
    api_key: str | None = None
    base_url: str | None = None
    kicad_cli_path: str | None = None
    db_last_scanned: str | None = None


def load_config() -> AgentConfig:
    if CONFIG_PATH.exists():
        return AgentConfig.model_validate(json.loads(CONFIG_PATH.read_text()))
    return AgentConfig()


def save_config(cfg: AgentConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2))


def sanitized_config() -> dict:
    cfg = load_config().model_dump()
    if cfg.get("api_key"):
        cfg["api_key"] = "***"
    return cfg
