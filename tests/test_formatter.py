import pytest
from datetime import datetime, timezone, timedelta
from src.models import DigestResult, ProcessedArticle
from src.formatter import format_digest

JST = timezone(timedelta(hours=9))

def make_digest(ai_count=2, pc_count=1, dry_run=False):
    now = datetime(2026, 5, 10, 7, 0, tzinfo=JST)
    ai = [
        ProcessedArticle(
            url=f"https://ai.com/{i}", title=f"AI Article {i}",
            ai_summary=f"AI要約{i}", source_name="TestAI",
            published_at=now, category="ai"
        ) for i in range(ai_count)
    ]
    pc = [
        ProcessedArticle(
            url=f"https://pc.com/{i}", title=f"PC Article {i}",
            ai_summary=f"PC要約{i}", source_name="TestPC",
            published_at=now, category="pc"
        ) for i in range(pc_count)
    ]
    return DigestResult(date=now, ai_articles=ai, pc_articles=pc, trend_summary="トレンドテスト", dry_run=dry_run)

def test_format_contains_date():
    digest = make_digest()
    output = format_digest(digest)
    assert "2026-05-10" in output

def test_format_contains_articles():
    digest = make_digest()
    output = format_digest(digest)
    assert "AI Article 0" in output
    assert "PC Article 0" in output

def test_format_empty_ai():
    digest = make_digest(ai_count=0)
    output = format_digest(digest)
    assert "## AI・機械学習" in output
    assert "該当記事がありませんでした" in output

def test_format_trend_appears():
    digest = make_digest()
    output = format_digest(digest)
    assert "トレンドテスト" in output

def test_format_markdown_structure():
    digest = make_digest()
    output = format_digest(digest)
    assert output.startswith("# ニュースダイジェスト")
    assert "## AI・機械学習" in output
    assert "## PC・ハードウェア" in output

def test_format_dry_run_marker():
    digest = make_digest(dry_run=True)
    output = format_digest(digest)
    assert "DRY RUN" in output
