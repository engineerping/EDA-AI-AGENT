import json, os, pytest
from pathlib import Path
from unittest.mock import patch

def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config
        cfg = load_config()
    assert cfg.model == "anthropic/claude-opus-4-7"
    assert cfg.api_key is None
    assert cfg.kicad_cli_path is None

def test_save_and_load_config(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config, save_config, AgentConfig
        original = load_config()
        original.model = "openai/gpt-4o"
        original.api_key = "sk-test-key"
        save_config(original)
        reloaded = load_config()
    assert reloaded.model == "openai/gpt-4o"
    assert reloaded.api_key == "sk-test-key"

def test_sanitized_config_masks_api_key(tmp_path):
    cfg_file = tmp_path / "config.json"
    with patch("backend.config.CONFIG_PATH", cfg_file):
        from backend.config import load_config, save_config, sanitized_config
        cfg = load_config()
        cfg.api_key = "sk-real-secret"
        save_config(cfg)
        safe = sanitized_config()
    assert safe["api_key"] == "***"
    assert safe["model"] == "anthropic/claude-opus-4-7"
