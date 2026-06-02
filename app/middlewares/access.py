"""Whitelist-доступ: пропускаем только владельцев из OWNER_IDS."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    """Пускает дальше только пользователей из whitelist. Пустой набор = пускаем всех."""

    def __init__(self, allowed_ids: frozenset[int]) -> None:
        self._allowed = allowed_ids
        if not allowed_ids:
            logger.warning(
                "OWNER_IDS пуст — бот доступен ВСЕМ. "
                "Укажи свой Telegram ID в .env, чтобы ограничить доступ."
            )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if self._allowed:
            user: User | None = data.get("event_from_user")
            if user is None or user.id not in self._allowed:
                logger.info("Доступ запрещён: %s", user.id if user else "unknown")
                if isinstance(event, Message):
                    await event.answer("⛔ Доступ ограничён.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Доступ ограничён.", show_alert=True)
                return None
        return await handler(event, data)
