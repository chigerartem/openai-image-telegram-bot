from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Database:
    """Тонкая обёртка над одним соединением aiosqlite + runner миграций."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        db_path = Path(self._path)
        if db_path.parent and not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = await aiosqlite.connect(self._path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA busy_timeout=5000")
        await conn.commit()
        self._conn = conn
        await self._run_migrations()
        logger.info("Database connected: %s", self._path)

    async def _run_migrations(self) -> None:
        conn = self.connection
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations ("
            "name TEXT PRIMARY KEY, "
            "applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        await conn.commit()

        async with conn.execute("SELECT name FROM _migrations") as cur:
            applied = {row["name"] for row in await cur.fetchall()}

        for sql_file in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            if sql_file.name in applied:
                continue
            logger.info("Applying migration: %s", sql_file.name)
            await conn.executescript(sql_file.read_text(encoding="utf-8"))
            await conn.execute(
                "INSERT INTO _migrations (name) VALUES (?)", (sql_file.name,)
            )
            await conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            logger.info("Database closed")

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected — call connect() first")
        return self._conn
