import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from src.models import RawArticle, ProcessedArticle
from src.summarizer import (
    summarize_articles,
    generate_trend_summary,
    NoLLMProvider,
    GeminiProvider,
    OllamaProvider,
    build_provider,
)


def make_raw(title: str = "Test Title", summary: str = "Test summary", category: str = "ai") -> RawArticle:
    return RawArticle(
        url="https://example.com/1",
        title=title,
        summary=summary,
        source_name="Test",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        category=category,
    )


def make_processed(title: str = "Test") -> ProcessedArticle:
    return ProcessedArticle(
        url="https://example.com/1",
        title=title,
        ai_summary="summary",
        source_name="Test",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        category="ai",
    )


# --- dry_run tests (no LLM calls) ---

def test_summarize_dry_run():
    provider = NoLLMProvider()
    articles = [make_raw(summary="This is a long summary text")]
    results = summarize_articles(articles, provider, dry_run=True)
    assert len(results) == 1
    assert "[DRY RUN]" in results[0].ai_summary


def test_trend_dry_run():
    provider = NoLLMProvider()
    ai = [make_processed("Claude released")]
    pc = [make_processed("RTX 5080")]
    result = generate_trend_summary(ai, pc, provider, dry_run=True)
    assert "[DRY RUN]" in result


# --- NoLLMProvider tests ---

def test_no_llm_truncates():
    provider = NoLLMProvider()
    long_text = "a" * 300
    assert len(provider.summarize_article("title", long_text)) <= 150


def test_no_llm_trend():
    provider = NoLLMProvider()
    result = provider.generate_trend(["AI article"], ["PC article"])
    assert "1" in result


# --- GeminiProvider tests (mocked) ---

def test_gemini_summarize_success():
    with patch("google.genai.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "要約テキストです。"
        MockClient.return_value = mock_client

        provider = GeminiProvider(api_key="DUMMY", model="gemini-2.0-flash")
        result = provider.summarize_article("Title", "Summary text")
        assert "要約テキストです" in result


def test_gemini_api_error_fallback():
    with patch("google.genai.Client") as MockClient:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        MockClient.return_value = mock_client

        provider = GeminiProvider(api_key="DUMMY")
        result = provider.summarize_article("Title", "Fallback summary text here")
        assert "Fallback" in result


# --- build_provider tests ---

def test_build_provider_none():
    cfg = MagicMock()
    cfg.provider = "none"
    provider = build_provider(cfg)
    assert isinstance(provider, NoLLMProvider)


def test_build_provider_gemini_missing_key():
    cfg = MagicMock()
    cfg.provider = "gemini"
    cfg.api_key = None
    with pytest.raises(ValueError):
        build_provider(cfg)
