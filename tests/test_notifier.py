import pytest
from pathlib import Path
from datetime import datetime
from src.notifier import write_digest_file, send_slack_notification, send_discord_notification

def test_write_digest_file(tmp_path):
    path = write_digest_file("# Test Content", str(tmp_path / "out"), datetime(2026, 5, 10))
    assert Path(path).exists()
    assert Path(path).read_text(encoding="utf-8") == "# Test Content"

def test_write_creates_output_dir(tmp_path):
    nested = tmp_path / "a" / "b" / "output"
    write_digest_file("content", str(nested), datetime(2026, 5, 10))
    assert nested.exists()

def test_slack_dry_run():
    result = send_slack_notification("https://dummy.url", "/path/to/digest.md", 5, dry_run=True)
    assert result is True

def test_discord_dry_run():
    result = send_discord_notification("https://dummy.url", "/path/to/digest.md", 5, dry_run=True)
    assert result is True

def test_slack_success(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value.raise_for_status = lambda: None
    result = send_slack_notification("https://hooks.slack.com/test", "/path.md", 3)
    assert result is True
    mock_post.assert_called_once()

def test_discord_success(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_post.return_value.raise_for_status = lambda: None
    result = send_discord_notification("https://discord.com/test", "/path.md", 3)
    assert result is True

def test_slack_http_error(mocker):
    mock_post = mocker.patch("httpx.post")
    mock_post.side_effect = Exception("connection refused")
    result = send_slack_notification("https://hooks.slack.com/test", "/path.md", 3)
    assert result is False
