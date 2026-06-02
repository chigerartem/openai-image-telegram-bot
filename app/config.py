"""Конфигурация бота из переменных окружения (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    """Неизменяемый снимок настроек, собранный при старте."""

    bot_token: str
    openai_api_key: str
    owner_ids: frozenset[int]
    openai_model: str  # модель по умолчанию для новых пользователей (меняется в /settings)
    db_path: str


def _parse_ids(raw: str) -> frozenset[int]:
    """«123, 456» → {123, 456}. Пустые и нечисловые токены пропускаются."""
    ids: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.add(int(chunk))
        except ValueError:
            continue
    return frozenset(ids)


def load_config() -> Config:
    """Читает .env и переменные окружения. Падает с понятной ошибкой, если нет ключей."""
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан — заполни .env")

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY не задан — заполни .env")

    return Config(
        bot_token=bot_token,
        openai_api_key=openai_api_key,
        owner_ids=_parse_ids(os.getenv("OWNER_IDS", "")),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-image-2").strip(),
        db_path=os.getenv("DB_PATH", "data/imagebot.db").strip(),
    )
