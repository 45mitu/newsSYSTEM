from __future__ import annotations
import argparse
import logging
import sys
from datetime import datetime

from src.config import load_config
from src.fetcher import fetch_all_feeds, SourceConfig as FetcherSourceConfig
from src.storage import ArticleStore
from src.filter import filter_articles
from src.summarizer import build_provider, summarize_articles, generate_trend_summary
from src.formatter import format_digest
from src.notifier import write_digest_file, send_slack_notification, send_discord_notification
from src.models import DigestResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(
    config_path: str = "config.yaml",
    env_path: str = ".env",
    dry_run: bool = False,
) -> int:
    logger.info("Starting news digest generation (dry_run=%s)", dry_run)
    try:
        config = load_config(config_path, env_path, dry_run=dry_run)
    except Exception as e:
        logger.error("Config load failed: %s", e)
        return 1

    # fetcher.pyのSourceConfigと互換性を持たせるため変換
    fetcher_sources = [
        FetcherSourceConfig(name=s.name, url=s.url, category=s.category)
        for s in config.sources
    ]

    with ArticleStore(config.db_path) as store:
        store.init_db()
        purged = store.purge_old(config.retention_days)
        if purged:
            logger.info("Purged %d old articles from DB", purged)

        raw_articles = fetch_all_feeds(
            fetcher_sources,
            timeout=config.fetch_timeout,
            dry_run=dry_run,
        )
        logger.info("Fetched %d raw articles", len(raw_articles))

        ai_raw, pc_raw = filter_articles(
            raw_articles,
            config.keywords_ai,
            config.keywords_pc,
            store,
            max_per_category=config.llm.max_articles_per_category,
        )
        logger.info("After filter: AI=%d, PC=%d", len(ai_raw), len(pc_raw))

        provider = build_provider(config.llm)

        ai_processed = summarize_articles(ai_raw, provider, dry_run=dry_run)
        pc_processed = summarize_articles(pc_raw, provider, dry_run=dry_run)
        trend = generate_trend_summary(ai_processed, pc_processed, provider, dry_run=dry_run)

        digest = DigestResult(
            date=datetime.now(),
            ai_articles=ai_processed,
            pc_articles=pc_processed,
            trend_summary=trend,
            dry_run=dry_run,
        )

        content = format_digest(digest)
        path = write_digest_file(content, config.notification.output_dir, digest.date, dry_run=dry_run)
        logger.info("Digest written to: %s", path)

        total = len(ai_processed) + len(pc_processed)
        if config.notification.slack_enabled and config.notification.slack_webhook_url:
            send_slack_notification(config.notification.slack_webhook_url, path, total, dry_run=dry_run)
        if config.notification.discord_enabled and config.notification.discord_webhook_url:
            send_discord_notification(config.notification.discord_webhook_url, path, total, dry_run=dry_run)

        if not dry_run:
            all_urls = [a.url for a in ai_processed + pc_processed]
            if all_urls:
                store.mark_sent(all_urls, sent_at=digest.date)
                logger.info("Marked %d URLs as sent", len(all_urls))

    logger.info("Done. Total articles: AI=%d, PC=%d", len(ai_processed), len(pc_processed))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ニュース自動配信システム")
    parser.add_argument("--config", default="config.yaml", help="設定ファイルのパス")
    parser.add_argument("--env", default=".env", help=".envファイルのパス")
    parser.add_argument("--dry-run", action="store_true", help="実際のAPI呼び出しをスキップ")
    args = parser.parse_args()
    sys.exit(main(args.config, args.env, args.dry_run))
