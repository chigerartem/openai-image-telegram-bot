from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.database import Database


class DbSessionMiddleware(BaseMiddleware):
    """Кладёт соединение с БД в data хендлеров под ключами `conn` и `db`."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["conn"] = self._db.connection
        data["db"] = self._db
        return await handler(event, data)
