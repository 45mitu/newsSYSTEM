from __future__ import annotations
from datetime import datetime, timezone, timedelta
from src.models import DigestResult, ProcessedArticle

JST = timezone(timedelta(hours=9))

def format_digest(digest: DigestResult) -> str:
    date_str = digest.date.astimezone(JST).strftime("%Y-%m-%d")
    generated_at = digest.date.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")

    lines = [
        f"# ニュースダイジェスト {date_str}",
        "",
        f"> 生成日時: {generated_at}",
    ]
    if digest.dry_run:
        lines.append("> ⚠️ DRY RUN モード（実際のニュースではありません）")
    lines.append("")

    lines += _format_section(digest.ai_articles, "AI・機械学習")
    lines.append("")
    lines += _format_section(digest.pc_articles, "PC・ハードウェア")
    lines += [
        "",
        "---",
        "## 本日のトレンドまとめ",
        "",
        digest.trend_summary,
        "",
        "---",
        "*このダイジェストは自動生成されました。*",
    ]
    return "\n".join(lines)

def _format_section(articles: list[ProcessedArticle], heading: str) -> list[str]:
    lines = [f"## {heading}", ""]
    if not articles:
        lines.append("*本日は該当記事がありませんでした。*")
        return lines
    for a in articles:
        pub = a.published_at.astimezone(JST).strftime("%Y-%m-%d %H:%M") if a.published_at.tzinfo else a.published_at.strftime("%Y-%m-%d %H:%M")
        lines += [
            f"### {a.title}",
            f"- **要約**: {a.ai_summary}",
            f"- **ソース**: {a.source_name} | **公開日時**: {pub} JST | **URL**: {a.url}",
            "",
        ]
    return lines
