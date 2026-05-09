import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.main import main

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
  ai: [Claude, GPT, LLM, Anthropic]
  pc: [Ryzen, Intel, AMD, RTX]
database:
  path: ""
  retention_days: 30
llm:
  provider: "none"
  model: ""
  max_articles_per_category: 5
  ollama_base_url: "http://localhost:11434"
  ollama_model: "qwen2.5:3b"
notification:
  output_dir: ""
  slack_enabled: false
  discord_enabled: false
fetch:
  timeout_seconds: 10
  user_agent: "TestBot/1.0"
"""
    p = tmp_path / "config.yaml"
    p.write_text(content, encoding="utf-8")
    return p, tmp_path

def test_main_dry_run_exits_zero(config_file, tmp_path):
    cfg_path, base = config_file
    env_path = base / ".env"
    env_path.write_text("GEMINI_API_KEY=DUMMY\n", encoding="utf-8")

    # db と output を tmp_path 内に向ける
    import yaml
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["database"]["path"] = str(base / "test.db")
    cfg["notification"]["output_dir"] = str(base / "output")
    cfg_path.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")

    result = main(str(cfg_path), str(env_path), dry_run=True)
    assert result == 0

def test_main_dry_run_creates_digest(config_file, tmp_path):
    cfg_path, base = config_file
    env_path = base / ".env"
    env_path.write_text("GEMINI_API_KEY=DUMMY\n", encoding="utf-8")

    import yaml
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["database"]["path"] = str(base / "test.db")
    output_dir = base / "output"
    cfg["notification"]["output_dir"] = str(output_dir)
    cfg_path.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")

    main(str(cfg_path), str(env_path), dry_run=True)
    digests = list(output_dir.glob("digest_*.md"))
    assert len(digests) >= 1

def test_main_dry_run_no_db_writes(config_file, tmp_path):
    cfg_path, base = config_file
    env_path = base / ".env"
    env_path.write_text("GEMINI_API_KEY=DUMMY\n", encoding="utf-8")

    import yaml, sqlite3
    cfg = yaml.safe_load(cfg_path.read_text())
    db_path = str(base / "test.db")
    cfg["database"]["path"] = db_path
    cfg["notification"]["output_dir"] = str(base / "output")
    cfg_path.write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")

    main(str(cfg_path), str(env_path), dry_run=True)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT COUNT(*) FROM sent_articles").fetchone()[0]
    conn.close()
    assert rows == 0
