import pytest
from datetime import datetime, timezone
from src.storage import ArticleStore


@pytest.fixture
def store(tmp_path):
    s = ArticleStore(str(tmp_path / "test.db"))
    s.init_db()
    yield s
    s.close()


def test_init_db_idempotent(store):
    store.init_db()  # 2回目も安全


def test_mark_and_is_seen(store):
    store.mark_sent(["https://example.com/1"])
    assert store.is_seen("https://example.com/1") is True


def test_is_seen_unknown_url(store):
    assert store.is_seen("https://unknown.com") is False


def test_mark_sent_idempotent(store):
    store.mark_sent(["https://example.com/1"])
    store.mark_sent(["https://example.com/1"])  # no error


def test_purge_old_removes_old(store, tmp_path):
    # 古いレコードを直接挿入してpurgeでテスト
    conn = store._get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sent_articles (url, sent_at) VALUES (?, ?)",
        ("https://old.com", "2020-01-01T00:00:00"),
    )
    conn.commit()
    deleted = store.purge_old(retention_days=30)
    assert deleted >= 1
    assert store.is_seen("https://old.com") is False


def test_purge_old_keeps_recent(store):
    store.mark_sent(["https://recent.com"])
    deleted = store.purge_old(retention_days=30)
    assert store.is_seen("https://recent.com") is True


def test_context_manager(tmp_path):
    with ArticleStore(str(tmp_path / "ctx.db")) as s:
        s.init_db()
        s.mark_sent(["https://ctx.com"])
        assert s.is_seen("https://ctx.com") is True
