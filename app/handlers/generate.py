"""Основной хендлер: текст → генерация изображения → отправка в чат."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import BufferedInputFile, Message

from app.db.repository import save_generation, upsert_user
from app.services.openai_image import ImageGenerationError, OpenAIImageService

logger = logging.getLogger(__name__)
router = Router()

_MAX_CAPTION = 1000


@router.message(F.text & ~F.text.startswith("/"))
async def handle_prompt(
    message: Message,
    conn: aiosqlite.Connection,
    image_service: OpenAIImageService,
) -> None:
    prompt = (message.text or "").strip()
    if not prompt:
        return

    user = message.from_user
    if user is not None:
        await upsert_user(conn, user.id, user.username, user.first_name)

    status = await message.answer("🎨 Генерирую изображение…")
    if message.bot is not None:
        await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    try:
        image_bytes = await image_service.generate(prompt)
    except ImageGenerationError as exc:
        await status.edit_text(f"⚠️ {exc}")
        if user is not None:
            await save_generation(
                conn, user.id, prompt, image_service.model,
                image_service.size, image_service.quality,
                status="error", error=str(exc),
            )
        return

    photo = BufferedInputFile(image_bytes, filename="image.png")
    caption = prompt if len(prompt) <= _MAX_CAPTION else prompt[: _MAX_CAPTION - 1] + "…"
    await message.answer_photo(photo, caption=caption)
    await status.delete()

    if user is not None:
        await save_generation(
            conn, user.id, prompt, image_service.model,
            image_service.size, image_service.quality,
        )
    logger.info("Сгенерировано для %s: %s", user.id if user else "?", prompt[:80])


@router.message()
async def handle_non_text(message: Message) -> None:
    await message.answer("✍️ Пришли текстовое описание картинки.")
