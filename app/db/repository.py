"""Доступ к данным: пользователи, история генераций и персональные настройки."""

from __future__ import annotations

import aiosqlite

from app.presets import UserSettings

# Поля user_settings, которые можно менять по одному из меню.
_SETTING_FIELDS = frozenset({"aspect", "quality", "model", "fidelity"})


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


async def get_settings(
    conn: aiosqlite.Connection, user_id: int, default_model: str | None = None
) -> UserSettings:
    """Возвращает настройки пользователя, создавая строку с дефолтами при первом обращении.

    ``default_model`` (если задан) используется как стартовая модель для новых
    пользователей — так бот уважает OPENAI_MODEL из .env.
    """
    async with conn.execute(
        "SELECT aspect, custom_w, custom_h, quality, model, fidelity "
        "FROM user_settings WHERE user_id = ?",
        (user_id,),
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        if default_model:
            await conn.execute(
                "INSERT INTO user_settings (user_id, model) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO NOTHING",
                (user_id, default_model),
            )
        else:
            await conn.execute(
                "INSERT INTO user_settings (user_id) VALUES (?) "
                "ON CONFLICT(user_id) DO NOTHING",
                (user_id,),
            )
        await conn.commit()
        async with conn.execute(
            "SELECT aspect, custom_w, custom_h, quality, model, fidelity "
            "FROM user_settings WHERE user_id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()

    return UserSettings(
        aspect=row["aspect"],
        custom_w=row["custom_w"],
        custom_h=row["custom_h"],
        quality=row["quality"],
        model=row["model"],
        fidelity=row["fidelity"],
    )


async def update_setting(
    conn: aiosqlite.Connection, user_id: int, field: str, value: str
) -> None:
    """Обновляет одно поле настроек. Имя поля валидируется по белому списку."""
    if field not in _SETTING_FIELDS:
        raise ValueError(f"Недопустимое поле настроек: {field}")
    await get_settings(conn, user_id)  # гарантируем наличие строки
    await conn.execute(
        f"UPDATE user_settings SET {field} = ?, updated_at = datetime('now') "
        "WHERE user_id = ?",
        (value, user_id),
    )
    await conn.commit()


async def set_custom_size(
    conn: aiosqlite.Connection, user_id: int, width: int, height: int
) -> None:
    """Ставит формат 'custom' и сохраняет точные размеры."""
    await get_settings(conn, user_id)
    await conn.execute(
        "UPDATE user_settings SET aspect = 'custom', custom_w = ?, custom_h = ?, "
        "updated_at = datetime('now') WHERE user_id = ?",
        (width, height, user_id),
    )
    await conn.commit()
