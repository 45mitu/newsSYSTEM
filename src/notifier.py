from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

def write_digest_file(
    content: str,
    output_dir: str,
    date: datetime,
    dry_run: bool = False,
) -> str:
    """output/digest_YYYY-MM-DD.md を書き出す。常に実行（dry_run でも）。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    filename = f"digest_{date.strftime('%Y-%m-%d')}.md"
    path = out / filename
    path.write_text(content, encoding="utf-8")
    logger.info("Digest written: %s", path)
    return str(path)

def send_slack_notification(
    webhook_url: str,
    digest_path: str,
    article_count: int,
    dry_run: bool = False,
) -> bool:
    if dry_run:
        logger.info("DRY RUN: would POST to Slack (%d articles)", article_count)
        return True
    payload = {
        "text": f"本日のニュースダイジェスト ({article_count}件) を生成しました。",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ニュースダイジェスト*: {article_count}件の記事をまとめました。\n`{digest_path}`",
                },
            }
        ],
    }
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning("Slack notification failed: %s", e)
        return False

def send_discord_notification(
    webhook_url: str,
    digest_path: str,
    article_count: int,
    dry_run: bool = False,
) -> bool:
    if dry_run:
        logger.info("DRY RUN: would POST to Discord (%d articles)", article_count)
        return True
    payload = {"content": f"**ニュースダイジェスト** ({article_count}件) を生成しました。"}
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning("Discord notification failed: %s", e)
        return False
