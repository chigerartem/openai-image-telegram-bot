"""Команды /start и /help."""

from __future__ import annotations

import aiosqlite
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.db.repository import upsert_user

router = Router()

_START_TEXT = (
    "👋 Привет! Я генерирую изображения через OpenAI.\n\n"
    "Просто пришли текстовое описание картинки — и я нарисую её.\n\n"
    "Например:\n"
    "<i>космонавт-кот на Луне, цифровая иллюстрация, мягкий свет</i>"
)

_HELP_TEXT = (
    "🖼 <b>Как пользоваться</b>\n\n"
    "Отправь текстовое описание — получишь картинку.\n"
    "Чем подробнее опишешь (стиль, свет, ракурс, детали), тем точнее результат.\n\n"
    "<b>Команды</b>\n"
    "/start — приветствие\n"
    "/help — эта справка"
)


@router.message(CommandStart())
async def cmd_start(message: Message, conn: aiosqlite.Connection) -> None:
    user = message.from_user
    if user is not None:
        await upsert_user(conn, user.id, user.username, user.first_name)
    await message.answer(_START_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP_TEXT)
