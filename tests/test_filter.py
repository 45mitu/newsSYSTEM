import pytest
from datetime import datetime, timezone
from src.models import RawArticle
from src.storage import ArticleStore
from src.filter import matches_keywords, filter_articles


@pytest.fixture
def store(tmp_path):
    s = ArticleStore(str(tmp_path / "filter_test.db"))
    s.init_db()
    yield s
    s.close()


def make_article(title: str, summary: str = "", category: str = "ai") -> RawArticle:
    return RawArticle(
        url=f"https://example.com/{title[:10]}",
        title=title,
        summary=summary,
        source_name="Test",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        category=category,
    )


def test_keyword_match_title():
    article = make_article("Claude 3.7 released by Anthropic")
    assert matches_keywords(article, ["Claude"]) is True


def test_keyword_match_summary():
    article = make_article("New model", "GPT-5 is now available")
    assert matches_keywords(article, ["GPT"]) is True


def test_keyword_case_insensitive():
    article = make_article("claude is great")
    assert matches_keywords(article, ["Claude"]) is True


def test_keyword_no_match():
    article = make_article("General news today")
    assert matches_keywords(article, ["Claude", "GPT"]) is False


def test_filter_dedup(store):
    article = make_article("Claude update", category="ai")
    store.mark_sent([article.url])
    ai, pc = filter_articles([article], ["Claude"], [], store)
    assert len(ai) == 0


def test_filter_new_article(store):
    article = make_article("Claude update", category="ai")
    ai, pc = filter_articles([article], ["Claude"], [], store)
    assert len(ai) == 1


def test_filter_both_categories(store):
    article = make_article("Intel AI chip with NVMe", category="ai")
    ai, pc = filter_articles([article], ["Intel"], ["NVMe"], store)
    assert len(ai) == 1
    assert len(pc) == 1


def test_filter_empty_input(store):
    ai, pc = filter_articles([], ["Claude"], ["Ryzen"], store)
    assert ai == []
    assert pc == []
