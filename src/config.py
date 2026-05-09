from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from dotenv import load_dotenv

from src.models import Category

@dataclass
class SourceConfig:
    name: str
    url: str
    category: Category

@dataclass
class LLMConfig:
    provider: str         # "gemini" | "ollama" | "none"
    model: str
    max_articles_per_category: int
    api_key: str | None   # GEMINI_API_KEY from env
    ollama_base_url: str
    ollama_model: str

@dataclass
class NotificationConfig:
    output_dir: str
    slack_enabled: bool
    discord_enabled: bool
    slack_webhook_url: str | None    # SLACK_WEBHOOK_URL from env
    discord_webhook_url: str | None  # DISCORD_WEBHOOK_URL from env

@dataclass
class GitHubPagesConfig:
    enabled: bool
    remote: str   # git remote name (e.g. "origin")
    branch: str   # e.g. "gh-pages"

@dataclass
class AppConfig:
    sources: list[SourceConfig]
    keywords_ai: list[str]
    keywords_pc: list[str]
    db_path: str
    retention_days: int
    llm: LLMConfig
    notification: NotificationConfig
    github_pages: GitHubPagesConfig
    fetch_timeout: int
    fetch_user_agent: str
    dry_run: bool = False

def load_config(
    config_path: str = "config.yaml",
    env_path: str = ".env",
    dry_run: bool = False,
) -> AppConfig:
    """config.yaml と .env を読み込み AppConfig を返す。"""
    load_dotenv(env_path)

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sources: list[SourceConfig] = []
    for cat, items in data.get("sources", {}).items():
        for item in items:
            sources.append(SourceConfig(
                name=item["name"],
                url=item["url"],
                category=cat,  # "ai" or "pc"
            ))

    llm_data = data.get("llm", {})
    provider = llm_data.get("provider", "gemini")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if provider == "gemini" and not dry_run and not gemini_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。.env ファイルを確認してください。")

    notif_data = data.get("notification", {})
    fetch_data = data.get("fetch", {})
    db_data = data.get("database", {})
    gh_data = data.get("github_pages", {})

    return AppConfig(
        sources=sources,
        keywords_ai=[str(k) for k in data.get("keywords", {}).get("ai", [])],
        keywords_pc=[str(k) for k in data.get("keywords", {}).get("pc", [])],
        db_path=db_data.get("path", "articles.db"),
        retention_days=int(db_data.get("retention_days", 30)),
        llm=LLMConfig(
            provider=provider,
            model=llm_data.get("model", "gemini-2.0-flash"),
            max_articles_per_category=int(llm_data.get("max_articles_per_category", 10)),
            api_key=gemini_key,
            ollama_base_url=llm_data.get("ollama_base_url", "http://localhost:11434"),
            ollama_model=llm_data.get("ollama_model", "qwen2.5:3b"),
        ),
        notification=NotificationConfig(
            output_dir=notif_data.get("output_dir", "output"),
            slack_enabled=bool(notif_data.get("slack_enabled", False)),
            discord_enabled=bool(notif_data.get("discord_enabled", False)),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        ),
        github_pages=GitHubPagesConfig(
            enabled=bool(gh_data.get("enabled", False)),
            remote=gh_data.get("remote", "origin"),
            branch=gh_data.get("branch", "gh-pages"),
        ),
        fetch_timeout=int(fetch_data.get("timeout_seconds", 30)),
        fetch_user_agent=fetch_data.get("user_agent", "NewsBot/1.0"),
        dry_run=dry_run,
    )
