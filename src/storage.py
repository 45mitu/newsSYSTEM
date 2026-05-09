import sqlite3
from datetime import datetime, timezone


class ArticleStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
        return self._conn

    def init_db(self) -> None:
        """テーブルとインデックスを作成。何度呼んでも安全。"""
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                sent_at TEXT NOT NULL,
                title TEXT,
                source TEXT,
                category TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sent_at ON sent_articles(sent_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON sent_articles(url)")
        conn.commit()

    def is_seen(self, url: str) -> bool:
        """URLがDBに存在するか確認。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM sent_articles WHERE url = ?", (url,)
        ).fetchone()
        return row is not None

    def mark_sent(
        self,
        urls: list[str],
        sent_at: datetime | None = None,
        articles: list | None = None,
    ) -> None:
        """URLを送信済みとして記録。INSERT OR IGNORE で冪等。"""
        if sent_at is None:
            sent_at = datetime.now(timezone.utc)
        sent_at_str = sent_at.isoformat()

        # articleリストをURLキーの辞書に変換
        article_map: dict[str, object] = {}
        if articles:
            for a in articles:
                article_map[a.url] = a

        conn = self._get_conn()
        for url in urls:
            a = article_map.get(url)
            title = getattr(a, "title", None) if a else None
            source = getattr(a, "source_name", None) if a else None
            category = getattr(a, "category", None) if a else None
            conn.execute(
                "INSERT OR IGNORE INTO sent_articles (url, sent_at, title, source, category) VALUES (?, ?, ?, ?, ?)",
                (url, sent_at_str, title, source, category),
            )
        conn.commit()

    def purge_old(self, retention_days: int = 30) -> int:
        """retention_days 日より古いレコードを削除。削除件数を返す。"""
        conn = self._get_conn()
        cur = conn.execute(
            f"DELETE FROM sent_articles WHERE sent_at < datetime('now', '-{retention_days} days')"
        )
        conn.commit()
        return cur.rowcount

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "ArticleStore":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
