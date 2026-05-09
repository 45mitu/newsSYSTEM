from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from src.models import RawArticle, ProcessedArticle

if TYPE_CHECKING:
    from src.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    def summarize_article(self, title: str, raw_summary: str) -> str:
        """100-150文字の日本語要約を返す。"""
        ...

    def generate_trend(self, ai_titles: list[str], pc_titles: list[str]) -> str:
        """200文字以内の全体トレンドまとめを返す。"""
        ...


class GeminiProvider:
    """Google Gemini APIを使う実装（google-genai SDK）。"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model_name = model

    def summarize_article(self, title: str, raw_summary: str) -> str:
        prompt = (
            "あなたはIT/AIニュースの要約専門家です。\n"
            f"以下の記事を100〜150文字の日本語で要約してください。\n"
            f"タイトル: {title}\n"
            f"内容: {raw_summary[:1000]}\n"
            "必ず100〜150文字以内で簡潔にまとめてください。"
        )
        try:
            response = self._client.models.generate_content(
                model=self._model_name, contents=prompt
            )
            return response.text.strip()[:200]
        except Exception as e:
            logger.warning("Gemini summarize error: %s", e)
            return raw_summary[:150]

    def generate_trend(self, ai_titles: list[str], pc_titles: list[str]) -> str:
        all_titles = "\n".join(f"- {t}" for t in ai_titles + pc_titles)
        prompt = (
            "あなたはITニュースのトレンド分析専門家です。\n"
            "本日のニュース一覧から全体のトレンドを200文字以内の日本語でまとめてください。\n"
            f"{all_titles}"
        )
        try:
            response = self._client.models.generate_content(
                model=self._model_name, contents=prompt
            )
            return response.text.strip()[:250]
        except Exception as e:
            logger.warning("Gemini trend error: %s", e)
            return "本日のトレンドを取得できませんでした。"


class OllamaProvider:
    """Ollama ローカルLLMを使う実装。"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:3b",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def _generate(self, prompt: str) -> str:
        import httpx

        try:
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            logger.warning("Ollama error: %s", e)
            return ""

    def summarize_article(self, title: str, raw_summary: str) -> str:
        result = self._generate(
            f"以下の記事を100〜150文字の日本語で要約してください。\nタイトル: {title}\n内容: {raw_summary[:1000]}"
        )
        return result[:200] if result else raw_summary[:150]

    def generate_trend(self, ai_titles: list[str], pc_titles: list[str]) -> str:
        all_titles = "\n".join(f"- {t}" for t in ai_titles + pc_titles)
        result = self._generate(
            f"本日のニュース一覧から全体のトレンドを200文字以内の日本語でまとめてください。\n{all_titles}"
        )
        return result[:250] if result else "本日のトレンドを取得できませんでした。"


class NoLLMProvider:
    """LLMなし。RSS本文を切り詰めるだけ。"""

    def summarize_article(self, title: str, raw_summary: str) -> str:
        return raw_summary[:150]

    def generate_trend(self, ai_titles: list[str], pc_titles: list[str]) -> str:
        total = len(ai_titles) + len(pc_titles)
        return f"本日はAI {len(ai_titles)}件、PC {len(pc_titles)}件、計{total}件のニュースを収集しました。"


def build_provider(llm_config: "LLMConfig") -> LLMProvider:
    """config に応じて適切な LLMProvider を返す。"""
    if llm_config.provider == "gemini":
        if not llm_config.api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        return GeminiProvider(api_key=llm_config.api_key, model=llm_config.model)
    elif llm_config.provider == "ollama":
        return OllamaProvider(base_url=llm_config.ollama_base_url, model=llm_config.ollama_model)
    else:
        return NoLLMProvider()


def summarize_articles(
    articles: list[RawArticle],
    provider: LLMProvider,
    dry_run: bool = False,
) -> list[ProcessedArticle]:
    """記事一覧を要約してProcessedArticleリストを返す。"""
    results = []
    for article in articles:
        if dry_run:
            summary = f"[DRY RUN] {article.summary[:120]}"
        else:
            summary = provider.summarize_article(article.title, article.summary)
        results.append(
            ProcessedArticle(
                url=article.url,
                title=article.title,
                ai_summary=summary,
                source_name=article.source_name,
                published_at=article.published_at,
                category=article.category,
            )
        )
    return results


def generate_trend_summary(
    ai_articles: list[ProcessedArticle],
    pc_articles: list[ProcessedArticle],
    provider: LLMProvider,
    dry_run: bool = False,
) -> str:
    """全体トレンドまとめを生成。"""
    if dry_run:
        return f"[DRY RUN] 本日はAI・PCニュース各{len(ai_articles)}/{len(pc_articles)}件を収集しました。"
    ai_titles = [a.title for a in ai_articles]
    pc_titles = [a.title for a in pc_articles]
    if not ai_titles and not pc_titles:
        return "本日は該当ニュースがありませんでした。"
    return provider.generate_trend(ai_titles, pc_titles)
