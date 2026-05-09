from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Category = Literal["ai", "pc"]


@dataclass
class RawArticle:
    url: str
    title: str
    summary: str
    source_name: str
    published_at: datetime
    category: Category


@dataclass
class ProcessedArticle:
    url: str
    title: str
    ai_summary: str
    source_name: str
    published_at: datetime
    category: Category


@dataclass
class DigestResult:
    date: datetime
    ai_articles: list[ProcessedArticle]
    pc_articles: list[ProcessedArticle]
    trend_summary: str
    dry_run: bool = False
