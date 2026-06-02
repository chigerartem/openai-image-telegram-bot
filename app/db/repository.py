"""Доступ к данным: пользователи и история генераций."""

from __future__ import annotations

import aiosqlite


async def upsert_user(
    conn: aiosqlite.Connection,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    """Создаёт пользователя или обновляет его имя/username."""
    await conn.execute(
        "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "username = excluded.username, first_name = excluded.first_name",
        (user_id, username, first_name),
    )
    await conn.commit()


async def save_generation(
    conn: aiosqlite.Connection,
    user_id: int,
    prompt: str,
    model: str,
    size: str,
    quality: str,
    status: str = "ok",
    error: str | None = None,
) -> None:
    """Записывает попытку генерации (успешную или с ошибкой) в историю."""
    await conn.execute(
        "INSERT INTO image_generations "
        "(user_id, prompt, model, size, quality, status, error) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, prompt, model, size, quality, status, error),
    )
    await conn.commit()
