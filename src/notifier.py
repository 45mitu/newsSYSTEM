from __future__ import annotations
import logging
import shutil
import subprocess
import tempfile
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

def write_html_files(
    index_html: str,
    manifest_json: str,
    sw_js: str,
    icon_svg: str,
    output_dir: str,
) -> None:
    """PWA用ファイルをoutput_dirに書き出す。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(index_html, encoding="utf-8")
    (out / "manifest.json").write_text(manifest_json, encoding="utf-8")
    (out / "sw.js").write_text(sw_js, encoding="utf-8")
    (out / "icon.svg").write_text(icon_svg, encoding="utf-8")
    logger.info("HTML files written to %s", output_dir)


def push_github_pages(
    output_dir: str,
    remote: str = "origin",
    branch: str = "gh-pages",
    dry_run: bool = False,
) -> bool:
    """output/のHTML/JSON/JS/SVGをgh-pagesブランチにpushする。"""
    if dry_run:
        logger.info("DRY RUN: would push to %s/%s", remote, branch)
        return True

    out = Path(output_dir).resolve()
    web_exts = {".html", ".json", ".js", ".svg", ".ico", ".png"}
    web_files = [f for f in out.iterdir() if f.suffix in web_exts]

    if not web_files:
        logger.warning("No web files found in %s", output_dir)
        return False

    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        git_root = Path(r.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger.error("Not a git repo: %s", e)
        return False

    worktree_path = git_root / ".gh-pages-wt"
    try:
        # Fetch remote branch (ignore error if branch doesn't exist yet)
        subprocess.run(
            ["git", "fetch", remote, f"{branch}:{branch}"],
            capture_output=True, cwd=git_root,
        )

        # Create orphan branch if it doesn't exist
        br_check = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            capture_output=True, cwd=git_root,
        )
        if br_check.returncode != 0:
            subprocess.run(
                ["git", "checkout", "--orphan", branch],
                capture_output=True, cwd=git_root, check=True,
            )
            subprocess.run(
                ["git", "rm", "-rf", "."],
                capture_output=True, cwd=git_root,
            )
            subprocess.run(
                ["git", "checkout", "master"],
                capture_output=True, cwd=git_root,
            )

        # Add worktree
        subprocess.run(
            ["git", "worktree", "add", "--force", str(worktree_path), branch],
            capture_output=True, text=True, cwd=git_root, check=True,
        )

        # Copy web files
        for f in web_files:
            shutil.copy2(f, worktree_path / f.name)

        # Commit
        subprocess.run(["git", "add", "-A"], cwd=worktree_path, check=True)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=worktree_path
        )
        if diff.returncode != 0:
            date_str = datetime.now().strftime("%Y-%m-%d")
            subprocess.run(
                ["git", "commit", "-m", f"Update digest {date_str}"],
                cwd=worktree_path, check=True,
            )
            subprocess.run(
                ["git", "push", remote, branch],
                cwd=worktree_path, check=True,
            )
            logger.info("Pushed to GitHub Pages (%s/%s)", remote, branch)
        else:
            logger.info("GitHub Pages: no changes to push")

        return True

    except Exception as e:
        logger.error("GitHub Pages push failed: %s", e)
        return False
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            capture_output=True, cwd=git_root,
        )


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
