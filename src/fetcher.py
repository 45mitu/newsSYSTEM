from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import httpx

from src.models import Category, RawArticle

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "NewsBot/1.0"}


@dataclass
class SourceConfig:
    name: str
    url: str
    category: Category


SAMPLE_ARTICLES: list[RawArticle] = [
    RawArticle(
        url="https://example.com/ai/openai-gpt5",
        title="OpenAI releases GPT-5 with improved reasoning",
        summary="OpenAI has announced GPT-5, featuring significantly improved reasoning capabilities.",
        source_name="Example AI News",
        published_at=datetime.now(),
        category="ai",
    ),
    RawArticle(
        url="https://example.com/ai/claude-3-7-coding",
        title="Claude 3.7 Sonnet excels at coding",
        summary="Anthropic's Claude 3.7 Sonnet sets new benchmarks on software engineering tasks.",
        source_name="Example AI News",
        published_at=datetime.now(),
        category="ai",
    ),
    RawArticle(
        url="https://example.com/ai/gemini-ultra-paper",
        title="Google DeepMind publishes Gemini Ultra paper",
        summary="DeepMind releases technical paper detailing Gemini Ultra's architecture and training.",
        source_name="Example AI News",
        published_at=datetime.now(),
        category="ai",
    ),
    RawArticle(
        url="https://example.com/pc/ryzen-9950x-benchmark",
        title="AMD Ryzen 9 9950X benchmark results",
        summary="The Ryzen 9 9950X delivers exceptional multi-core performance in early benchmarks.",
        source_name="Example PC News",
        published_at=datetime.now(),
        category="pc",
    ),
    RawArticle(
        url="https://example.com/pc/rtx-5080-ti-specs",
        title="RTX 5080 Ti leaked specs",
        summary="Leaked specifications suggest the RTX 5080 Ti will feature 24 GB GDDR7 memory.",
        source_name="Example PC News",
        published_at=datetime.now(),
        category="pc",
    ),
    RawArticle(
        url="https://example.com/pc/ddr5-8000-pricing",
        title="DDR5-8000 pricing drops significantly",
        summary="DDR5-8000 memory kits see a 30% price reduction as supply stabilizes.",
        source_name="Example PC News",
        published_at=datetime.now(),
        category="pc",
    ),
]


def _parse_published(entry: dict) -> datetime:
    parsed = entry.get("published_parsed")
    if parsed is not None:
        return datetime(*parsed[:6])
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fetch_feed(source: SourceConfig, timeout: int = 30) -> list[RawArticle]:
    """1つのRSSフィードを取得。エラーは空リスト返却でsilentに処理。"""
    try:
        response = httpx.get(source.url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as exc:
        logger.warning("Failed to fetch feed %s: %s", source.url, exc)
        return []

    articles: list[RawArticle] = []
    for entry in feed.entries:
        try:
            url = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            published_at = _parse_published(entry)
            articles.append(
                RawArticle(
                    url=url,
                    title=title,
                    summary=summary,
                    source_name=source.name,
                    published_at=published_at,
                    category=source.category,
                )
            )
        except Exception as exc:
            logger.warning("Failed to parse entry from %s: %s", source.url, exc)

    return articles


def fetch_all_feeds(
    sources: list[SourceConfig],
    timeout: int = 30,
    dry_run: bool = False,
) -> list[RawArticle]:
    """全ソースを取得。dry_run=True なら SAMPLE_ARTICLES を返す。"""
    if dry_run:
        return SAMPLE_ARTICLES

    articles: list[RawArticle] = []
    for source in sources:
        articles.extend(fetch_feed(source, timeout=timeout))
    return articles
