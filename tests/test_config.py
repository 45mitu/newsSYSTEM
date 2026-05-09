import pytest
import os
from pathlib import Path
from src.config import load_config

@pytest.fixture
def config_file(tmp_path):
    content = """
sources:
  ai:
    - name: "Test AI"
      url: "https://example.com/ai.xml"
  pc:
    - name: "Test PC"
      url: "https://example.com/pc.xml"
keywords:
  ai: [Claude, GPT]
  pc: [Ryzen, Intel]
database:
  path: "test.db"
  retention_days: 7
llm:
  provider: "none"
  model: ""
  max_articles_per_category: 5
  ollama_base_url: "http://localhost:11434"
  ollama_model: "qwen2.5:3b"
notification:
  output_dir: "output"
  slack_enabled: false
  discord_enabled: false
fetch:
  timeout_seconds: 10
  user_agent: "TestBot/1.0"
"""
    p = tmp_path / "config.yaml"
    p.write_text(content, encoding="utf-8")
    return str(p)

@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("GEMINI_API_KEY=DUMMY\n", encoding="utf-8")
    return str(p)

def test_load_valid_config(config_file, env_file):
    config = load_config(config_file, env_file, dry_run=True)
    assert len(config.sources) == 2
    assert config.keywords_ai == ["Claude", "GPT"]
    assert config.keywords_pc == ["Ryzen", "Intel"]
    assert config.db_path == "test.db"
    assert config.retention_days == 7
    assert config.llm.provider == "none"
    assert config.fetch_timeout == 10

def test_missing_gemini_key_raises(config_file, tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    empty_env = str(tmp_path / "empty.env")
    Path(empty_env).write_text("", encoding="utf-8")
    # provider=none なのでキーがなくてもOK、かつ環境変数をクリアして api_key は None
    config = load_config(config_file, empty_env, dry_run=False)
    assert config.llm.api_key is None

def test_dry_run_no_key_required(config_file, tmp_path):
    empty_env = str(tmp_path / "empty.env")
    Path(empty_env).write_text("GEMINI_API_KEY=\n", encoding="utf-8")
    # dry_run=True なら gemini でもキーなしで通過
    config_content = Path(config_file).read_text().replace('provider: "none"', 'provider: "gemini"')
    cfg2 = tmp_path / "config2.yaml"
    cfg2.write_text(config_content, encoding="utf-8")
    config = load_config(str(cfg2), empty_env, dry_run=True)
    assert config.dry_run is True

def test_source_categories(config_file, env_file):
    config = load_config(config_file, env_file, dry_run=True)
    categories = {s.category for s in config.sources}
    assert "ai" in categories
    assert "pc" in categories
