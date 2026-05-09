from src.models import RawArticle, Category
from src.storage import ArticleStore


def matches_keywords(article: RawArticle, keywords: list[str]) -> bool:
    """タイトル+サマリの大文字小文字無視の部分一致チェック。"""
    text = (article.title + " " + article.summary).lower()
    return any(kw.lower() in text for kw in keywords)


def filter_articles(
    articles: list[RawArticle],
    keywords_ai: list[str],
    keywords_pc: list[str],
    store: ArticleStore,
    max_per_category: int = 10,
) -> tuple[list[RawArticle], list[RawArticle]]:
    """
    1. キーワードでフィルタ（AI/PC独立）
    2. store.is_seen() で重複排除
    3. max_per_category 件に上限
    AIとPCの両方にマッチする記事は両リストに含まれる（意図的）
    Returns: (ai_articles, pc_articles)
    """
    ai_articles: list[RawArticle] = []
    pc_articles: list[RawArticle] = []

    for article in articles:
        if store.is_seen(article.url):
            continue

        if keywords_ai and matches_keywords(article, keywords_ai):
            if len(ai_articles) < max_per_category:
                ai_articles.append(article)

        if keywords_pc and matches_keywords(article, keywords_pc):
            if len(pc_articles) < max_per_category:
                pc_articles.append(article)

    return ai_articles, pc_articles
