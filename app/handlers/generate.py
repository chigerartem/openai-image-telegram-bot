"""Основной хендлер: текст (или текст + референс) → генерация → отправка в чат."""

from __future__ import annotations

import asyncio
import logging

import aiosqlite
from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.types import BufferedInputFile, Message

from app.db.repository import get_settings, save_generation, upsert_user
from app.presets import RenderPlan, UserSettings, plan_render
from app.services.image_processing import crop_to_ratio, fit_to_size, to_png
from app.services.openai_image import ImageGenerationError, OpenAIImageService

logger = logging.getLogger(__name__)
router = Router()

_MAX_CAPTION = 1000


@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def handle_prompt(
    message: Message,
    conn: aiosqlite.Connection,
    image_service: OpenAIImageService,
) -> None:
    prompt = (message.text or "").strip()
    if not prompt:
        return
    await _run(message, conn, image_service, prompt, references=None)


@router.message(F.photo, StateFilter(None))
async def handle_photo(
    message: Message,
    conn: aiosqlite.Connection,
    image_service: OpenAIImageService,
) -> None:
    prompt = (message.caption or "").strip()
    if not prompt:
        await message.answer(
            "🖼 Это будет референс. Добавь к фото подпись — что с ним сделать "
            "(например: «в стиле акварели» или «поставь этого кота на Луну»)."
        )
        return

    if message.bot is None or not message.photo:
        return
    buffer = await message.bot.download(message.photo[-1])
    reference = to_png(buffer.read()) if buffer is not None else None
    if reference is None:
        await message.answer("⚠️ Не удалось скачать фото, попробуй ещё раз.")
        return
    await _run(message, conn, image_service, prompt, references=[reference])


async def _run(
    message: Message,
    conn: aiosqlite.Connection,
    image_service: OpenAIImageService,
    prompt: str,
    references: list[bytes] | None,
) -> None:
    user = message.from_user
    default_model = image_service.default_model
    if user is not None:
        await upsert_user(conn, user.id, user.username, user.first_name)
        settings = await get_settings(conn, user.id, default_model)
    else:
        settings = await get_settings(conn, message.chat.id, default_model)

    plan = plan_render(settings)

    status = await message.answer(
        "🎨 Рисую по референсу…" if references else "🎨 Генерирую изображение…"
    )
    if message.bot is not None:
        await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    try:
        if references:
            raw = await image_service.edit(
                prompt,
                references,
                model=settings.model,
                size=plan.api_size,
                quality=settings.quality,
                input_fidelity=settings.fidelity,
            )
        else:
            raw = await image_service.generate(
                prompt,
                model=settings.model,
                size=plan.api_size,
                quality=settings.quality,
            )
    except ImageGenerationError as exc:
        await status.edit_text(f"⚠️ {exc}")
        if user is not None:
            await save_generation(
                conn, user.id, prompt, settings.model,
                _size_label(settings, plan), settings.quality,
                status="error", error=str(exc),
            )
        return

    image_bytes = await asyncio.to_thread(_postprocess, raw, plan)

    photo = BufferedInputFile(image_bytes, filename="image.png")
    caption = prompt if len(prompt) <= _MAX_CAPTION else prompt[: _MAX_CAPTION - 1] + "…"
    await message.answer_photo(photo, caption=caption)
    await status.delete()

    if user is not None:
        await save_generation(
            conn, user.id, prompt, settings.model,
            _size_label(settings, plan), settings.quality,
        )
    logger.info("Сгенерировано для %s: %s", user.id if user else "?", prompt[:80])


def _postprocess(raw: bytes, plan: RenderPlan) -> bytes:
    """Применяет обрезку/подгон под выбранный формат (CPU-работа, в отдельном потоке)."""
    if plan.exact_size:
        return fit_to_size(raw, *plan.exact_size)
    if plan.crop_ratio:
        return crop_to_ratio(raw, *plan.crop_ratio)
    return raw


def _size_label(settings: UserSettings, plan: RenderPlan) -> str:
    """Человекочитаемый размер для записи в историю."""
    if plan.exact_size:
        return f"{plan.exact_size[0]}x{plan.exact_size[1]}"
    if plan.crop_ratio:
        return f"{settings.aspect} ({plan.api_size})"
    return plan.api_size


@router.message(StateFilter(None))
async def handle_unsupported(message: Message) -> None:
    await message.answer("✍️ Пришли текстовое описание картинки или фото с подписью-референсом.")
