"""Меню /settings: инлайн-кнопки для формата, качества, модели и силы референса."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app import keyboards as kb
from app.db.repository import get_settings, set_custom_size, update_setting
from app.presets import CUSTOM_MAX, CUSTOM_MIN, parse_custom_size

logger = logging.getLogger(__name__)
router = Router()


class SettingsSG(StatesGroup):
    custom_size = State()


# Какое подменю рисовать для каждой группы.
_SUBMENUS = {
    "aspect": kb.aspect_menu,
    "quality": kb.quality_menu,
    "model": kb.model_menu,
    "fidelity": kb.fidelity_menu,
}


@router.message(Command("settings"))
async def cmd_settings(message: Message, conn: aiosqlite.Connection) -> None:
    user = message.from_user
    if user is None:
        return
    settings = await get_settings(conn, user.id)
    await message.answer(kb.settings_summary(settings), reply_markup=kb.main_menu(settings))


@router.callback_query(F.data == f"{kb.CB_PREFIX}:close")
async def cb_close(query: CallbackQuery) -> None:
    if isinstance(query.message, Message):
        await query.message.delete()
    await query.answer("Закрыто")


@router.callback_query(F.data == f"{kb.CB_PREFIX}:menu")
async def cb_menu(query: CallbackQuery, conn: aiosqlite.Connection) -> None:
    await _render_main(query, conn)


@router.callback_query(F.data.startswith(f"{kb.CB_PREFIX}:open:"))
async def cb_open(query: CallbackQuery, conn: aiosqlite.Connection) -> None:
    group = query.data.split(":")[2]
    builder = _SUBMENUS.get(group)
    if builder is None or query.from_user is None:
        await query.answer()
        return
    settings = await get_settings(conn, query.from_user.id)
    if isinstance(query.message, Message):
        await query.message.edit_reply_markup(reply_markup=builder(settings))
    await query.answer()


@router.callback_query(F.data.startswith(f"{kb.CB_PREFIX}:set:"))
async def cb_set(query: CallbackQuery, conn: aiosqlite.Connection) -> None:
    _, _, field, value = query.data.split(":", 3)
    if query.from_user is None:
        await query.answer()
        return
    await update_setting(conn, query.from_user.id, field, value)
    await _render_main(query, conn)
    await query.answer("Сохранено ✅")


@router.callback_query(F.data == f"{kb.CB_PREFIX}:custom")
async def cb_custom(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsSG.custom_size)
    if isinstance(query.message, Message):
        await query.message.edit_text(
            "✏️ Пришли своё разрешение в формате <b>ширина×высота</b>, "
            f"например <code>1920x1080</code>.\n\n"
            f"Допустимо от {CUSTOM_MIN} до {CUSTOM_MAX} px по каждой стороне.\n"
            "Бот сгенерирует ближайший нативный формат и подгонит под точный размер.",
            reply_markup=kb.back_button(),
        )
    await query.answer()


@router.message(StateFilter(SettingsSG.custom_size), F.text)
async def on_custom_size(
    message: Message, state: FSMContext, conn: aiosqlite.Connection
) -> None:
    size = parse_custom_size(message.text or "")
    if size is None:
        await message.answer(
            "Не понял размер. Пример: <code>1920x1080</code> "
            f"(каждая сторона {CUSTOM_MIN}–{CUSTOM_MAX} px)."
        )
        return
    width, height = size
    user = message.from_user
    if user is None:
        return
    await set_custom_size(conn, user.id, width, height)
    await state.clear()
    settings = await get_settings(conn, user.id)
    await message.answer(
        f"Готово — формат теперь <b>{width}×{height}</b>.",
        reply_markup=kb.main_menu(settings),
    )


async def _render_main(query: CallbackQuery, conn: aiosqlite.Connection) -> None:
    if query.from_user is None:
        return
    settings = await get_settings(conn, query.from_user.id)
    if isinstance(query.message, Message):
        await query.message.edit_text(
            kb.settings_summary(settings), reply_markup=kb.main_menu(settings)
        )
