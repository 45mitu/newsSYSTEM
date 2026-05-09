from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import httpx
import pytest

from src.fetcher import SAMPLE_ARTICLES, SourceConfig, fetch_all_feeds, fetch_feed

_MINIMAL_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <item>
      <title>Test Article</title>
      <link>https://example.com/article-1</link>
      <description>A short summary.</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""

_RSS_NO_PUBDATE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <item>
      <title>No Date Article</title>
      <link>https://example.com/no-date</link>
      <description>No date here.</description>
    </item>
  </channel>
</rss>"""

_SOURCE_AI = SourceConfig(name="Test AI", url="https://example.com/ai.rss", category="ai")
_SOURCE_PC = SourceConfig(name="Test PC", url="https://example.com/pc.rss", category="pc")


def _mock_response(content: bytes) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.raise_for_status.return_value = None
    return resp


def test_fetch_all_feeds_dry_run():
    """dry_run=True なら SAMPLE_ARTICLES が返される"""
    result = fetch_all_feeds(sources=[], dry_run=True)
    assert result is SAMPLE_ARTICLES
    assert len(result) == 6
    ai_count = sum(1 for a in result if a.category == "ai")
    pc_count = sum(1 for a in result if a.category == "pc")
    assert ai_count == 3
    assert pc_count == 3


def test_fetch_feed_success(mocker):
    """正常なRSSレスポンスを httpx.get でモックし、RawArticle リストが返る"""
    mocker.patch("httpx.get", return_value=_mock_response(_MINIMAL_RSS))

    result = fetch_feed(_SOURCE_AI)

    assert len(result) == 1
    article = result[0]
    assert article.url == "https://example.com/article-1"
    assert article.title == "Test Article"
    assert article.summary == "A short summary."
    assert article.source_name == "Test AI"
    assert article.category == "ai"
    assert isinstance(article.published_at, datetime)


def test_fetch_feed_timeout(mocker):
    """httpx.TimeoutException が起きても空リストが返り例外は伝搬しない"""
    mocker.patch("httpx.get", side_effect=httpx.TimeoutException("timed out"))

    result = fetch_feed(_SOURCE_AI)

    assert result == []


def test_fetch_feed_http_error(mocker):
    """HTTPStatusError (404等) でも空リストが返る"""
    resp = MagicMock()
    resp.content = b""
    resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock()
    )
    mocker.patch("httpx.get", return_value=resp)

    result = fetch_feed(_SOURCE_AI)

    assert result == []


def test_fetch_feed_missing_published(mocker):
    """published_parsed が None のエントリは datetime.utcnow() でフォールバック"""
    mocker.patch("httpx.get", return_value=_mock_response(_RSS_NO_PUBDATE))

    result = fetch_feed(_SOURCE_AI)

    assert len(result) == 1
    assert isinstance(result[0].published_at, datetime)


def test_fetch_all_feeds_aggregates(mocker):
    """複数ソースの結果が結合される"""
    mocker.patch("httpx.get", return_value=_mock_response(_MINIMAL_RSS))

    result = fetch_all_feeds(sources=[_SOURCE_AI, _SOURCE_PC])

    assert len(result) == 2
    categories = {a.category for a in result}
    assert categories == {"ai", "pc"}
