from __future__ import annotations
import html
from datetime import datetime, timezone, timedelta
from src.models import DigestResult, ProcessedArticle

JST = timezone(timedelta(hours=9))

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#6c63ff">
  <title>ニュースダイジェスト {date_str}</title>
  <link rel="manifest" href="manifest.json">
  <style>
    :root{{--bg:#0f0f1a;--card:#1a1a2e;--text:#e0e0f0;--muted:#8888bb;--ai:#6c63ff;--pc:#00b4d8;--trend:#f72585;--border:#2a2a45;--link:#90e0ef}}
    @media(prefers-color-scheme:light){{:root{{--bg:#f4f4ff;--card:#fff;--text:#1a1a35;--muted:#5555aa;--border:#dde;--link:#005f8f}}}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;background:var(--bg);color:var(--text);max-width:720px;margin:0 auto;padding:16px 16px 80px}}
    header{{padding:20px 0 14px;border-bottom:1px solid var(--border);margin-bottom:24px}}
    .title{{font-size:1.4rem;font-weight:700;display:flex;align-items:center;gap:8px}}
    .date-badge{{background:var(--ai);color:#fff;font-size:.75rem;font-weight:600;padding:2px 10px;border-radius:20px}}
    .meta{{font-size:.75rem;color:var(--muted);margin-top:6px}}
    .dry-run{{background:#4a2e00;color:#ffcc00;border-radius:8px;padding:8px 14px;margin-bottom:16px;font-size:.82rem}}
    section{{margin-bottom:28px}}
    .sec-head{{display:flex;align-items:center;gap:8px;margin-bottom:14px}}
    .sec-head h2{{font-size:1rem;font-weight:700}}
    .dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
    .dot-ai{{background:var(--ai)}}.dot-pc{{background:var(--pc)}}.dot-trend{{background:var(--trend)}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:10px}}
    .card h3{{font-size:.92rem;font-weight:600;line-height:1.45;margin-bottom:8px}}
    .summary{{font-size:.83rem;color:var(--muted);line-height:1.65;margin-bottom:10px}}
    .art-meta{{font-size:.73rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
    .art-meta a{{color:var(--link);text-decoration:none;padding:2px 8px;border:1px solid var(--link);border-radius:20px;white-space:nowrap}}
    .trend-card{{background:var(--card);border:1px solid var(--trend);border-radius:12px;padding:14px}}
    .trend-card p{{font-size:.9rem;line-height:1.75}}
    footer{{margin-top:24px;padding-top:16px;border-top:1px solid var(--border);font-size:.72rem;color:var(--muted);text-align:center}}
    #install{{display:none;position:fixed;bottom:20px;right:20px;background:var(--ai);color:#fff;border:none;border-radius:24px;padding:12px 18px;font-size:.88rem;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(108,99,255,.5);z-index:99}}
  </style>
</head>
<body>
{dry_run_banner}
<header>
  <div class="title">📰 ニュースダイジェスト <span class="date-badge">{date_str}</span></div>
  <div class="meta">生成: {generated_at}</div>
</header>
<main>
{ai_section}
{pc_section}
<section>
  <div class="sec-head"><span class="dot dot-trend"></span><h2>本日のトレンドまとめ</h2></div>
  <div class="trend-card"><p>{trend_summary}</p></div>
</section>
</main>
<footer>このダイジェストは自動生成されました。</footer>
<button id="install">ホーム画面に追加</button>
<script>
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js');
let deferredPrompt;
window.addEventListener('beforeinstallprompt',e=>{{e.preventDefault();deferredPrompt=e;document.getElementById('install').style.display='block'}});
document.getElementById('install').addEventListener('click',()=>{{deferredPrompt.prompt();deferredPrompt.userChoice.then(()=>{{document.getElementById('install').style.display='none'}})}});
</script>
</body>
</html>"""

_MANIFEST = """\
{{
  "name": "AIニュースダイジェスト",
  "short_name": "AIニュース",
  "description": "AI・PCハードウェアの毎日ニュースダイジェスト",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#0f0f1a",
  "theme_color": "#6c63ff",
  "icons": [{{"src":"icon.svg","sizes":"any","type":"image/svg+xml","purpose":"any maskable"}}]
}}"""

_SW = """\
const CACHE='news-v{cache_key}';
const URLS=['./index.html','./manifest.json','./icon.svg'];
self.addEventListener('install',e=>{{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(URLS)).then(()=>self.skipWaiting()))}});
self.addEventListener('activate',e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))))}});
self.addEventListener('fetch',e=>{{e.respondWith(fetch(e.request).then(r=>{{const c=r.clone();caches.open(CACHE).then(ca=>ca.put(e.request,c));return r}}).catch(()=>caches.match(e.request)))}});"""

_ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
  <rect width="192" height="192" rx="32" fill="#6c63ff"/>
  <text x="96" y="135" font-size="100" text-anchor="middle" fill="white">📰</text>
</svg>"""


def format_digest_html(digest: DigestResult) -> tuple[str, str, str, str]:
    """HTML, manifest.json, sw.js, icon.svg を返す。"""
    date_str = digest.date.astimezone(JST).strftime("%Y-%m-%d")
    generated_at = digest.date.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")
    cache_key = digest.date.astimezone(JST).strftime("%Y%m%d")

    dry_run_banner = ""
    if digest.dry_run:
        dry_run_banner = '<div class="dry-run">⚠️ DRY RUN モード（実際のニュースではありません）</div>'

    ai_sec = _section_html(digest.ai_articles, "AI・機械学習", "ai")
    pc_sec = _section_html(digest.pc_articles, "PC・ハードウェア", "pc")

    index_html = _HTML_TEMPLATE.format(
        date_str=date_str,
        generated_at=generated_at,
        dry_run_banner=dry_run_banner,
        ai_section=ai_sec,
        pc_section=pc_sec,
        trend_summary=html.escape(digest.trend_summary),
    )
    sw_js = _SW.format(cache_key=cache_key)
    return index_html, _MANIFEST, sw_js, _ICON_SVG


def _section_html(articles: list[ProcessedArticle], heading: str, kind: str) -> str:
    if not articles:
        body = '<div class="card"><p style="color:var(--muted);font-size:.85rem">本日は該当記事がありませんでした。</p></div>'
    else:
        cards = []
        for a in articles:
            pub = (a.published_at.astimezone(JST).strftime("%m/%d %H:%M")
                   if a.published_at.tzinfo else a.published_at.strftime("%m/%d %H:%M"))
            cards.append(
                f'<div class="card">'
                f'<h3>{html.escape(a.title)}</h3>'
                f'<p class="summary">{html.escape(a.ai_summary)}</p>'
                f'<div class="art-meta">'
                f'<span>{html.escape(a.source_name)}</span>'
                f'<span>{pub} JST</span>'
                f'<a href="{html.escape(a.url)}" target="_blank" rel="noopener">記事を開く ↗</a>'
                f'</div></div>'
            )
        body = "\n".join(cards)

    emoji = "🤖" if kind == "ai" else "💻"
    return (
        f'<section>\n'
        f'<div class="sec-head"><span class="dot dot-{kind}"></span>'
        f'<h2>{emoji} {html.escape(heading)}</h2></div>\n'
        f'{body}\n</section>'
    )


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
