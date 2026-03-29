import sqlite3
from pathlib import Path


class IndexState:
    """Tracks pageid → revid for the last successfully indexed version of each page."""

    def __init__(self, path: str | Path) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS index_state (pageid TEXT PRIMARY KEY, revid INTEGER NOT NULL)"
        )
        self._conn.commit()

    def is_stale(self, pageid: str, revid: int) -> bool:
        """Return True if the page is new or has a different revid than what's indexed."""
        row = self._conn.execute(
            "SELECT revid FROM index_state WHERE pageid = ?", (pageid,)
        ).fetchone()
        return row is None or row[0] != revid

    def update(self, pageid: str, revid: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO index_state (pageid, revid) VALUES (?, ?)",
            (pageid, revid),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
