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
    "• Пришли <b>текстовое описание</b> — нарисую картинку.\n"
    "• Пришли <b>фото с подписью</b> — использую его как референс.\n"
    "• Формат, качество и модель настраиваются в /settings.\n\n"
    "Например:\n"
    "<i>космонавт-кот на Луне, цифровая иллюстрация, мягкий свет</i>"
)

_HELP_TEXT = (
    "🖼 <b>Как пользоваться</b>\n\n"
    "<b>Текст → картинка.</b> Отправь описание — получишь изображение. "
    "Чем подробнее (стиль, свет, ракурс, детали), тем точнее результат.\n\n"
    "<b>Фото → картинка.</b> Прикрепи фото и в подписи напиши, что с ним сделать "
    "(«в стиле акварели», «помести на Луну»). Силу следования референсу можно "
    "поднять в /settings.\n\n"
    "<b>Формат.</b> В /settings выбери 1:1, 3:2, 2:3, 16:9, 9:16 или своё разрешение "
    "(например 1920×1080).\n\n"
    "<b>Команды</b>\n"
    "/start — приветствие\n"
    "/settings — формат, качество, модель, референс\n"
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
