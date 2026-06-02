"""Инлайн-клавиатуры меню /settings.

Схема callback_data: ``s:<action>[:<value>]``
  s:menu                — главное меню
  s:open:<group>        — подменю (aspect|quality|model|fidelity)
  s:set:<group>:<value> — выбрать значение
  s:custom              — запросить своё разрешение
  s:close               — закрыть меню
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.presets import (
    ASPECTS,
    FIDELITIES,
    FIDELITY_LABELS,
    MODELS,
    QUALITIES,
    QUALITY_LABELS,
    UserSettings,
)

CB_PREFIX = "s"

_CHECK = "✅ "


def _mark(label: str, selected: bool) -> str:
    return f"{_CHECK}{label}" if selected else label


def settings_summary(s: UserSettings) -> str:
    """Текстовая шапка меню с текущими значениями."""
    return (
        "⚙️ <b>Настройки генерации</b>\n\n"
        f"📐 Формат: <b>{s.aspect_label()}</b>\n"
        f"✨ Качество: <b>{s.quality_label()}</b>\n"
        f"🧠 Модель: <b>{s.model}</b>\n"
        f"🎯 Сила референса: <b>{s.fidelity_label()}</b>\n\n"
        "Выбери, что изменить:"
    )


def main_menu(s: UserSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"📐 Формат · {s.aspect_label()}", callback_data=f"{CB_PREFIX}:open:aspect")
    kb.button(text=f"✨ Качество · {s.quality_label()}", callback_data=f"{CB_PREFIX}:open:quality")
    kb.button(text=f"🧠 Модель · {s.model}", callback_data=f"{CB_PREFIX}:open:model")
    kb.button(
        text=f"🎯 Референс · {s.fidelity_label()}",
        callback_data=f"{CB_PREFIX}:open:fidelity",
    )
    kb.button(text="✖ Закрыть", callback_data=f"{CB_PREFIX}:close")
    kb.adjust(1)
    return kb.as_markup()


def aspect_menu(s: UserSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, aspect in ASPECTS.items():
        kb.button(
            text=_mark(aspect.label, s.aspect == key),
            callback_data=f"{CB_PREFIX}:set:aspect:{key}",
        )
    kb.button(
        text=_mark("Своё ✏️", s.aspect == "custom"),
        callback_data=f"{CB_PREFIX}:custom",
    )
    kb.button(text="‹ Назад", callback_data=f"{CB_PREFIX}:menu")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def quality_menu(s: UserSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for q in QUALITIES:
        kb.button(
            text=_mark(QUALITY_LABELS[q], s.quality == q),
            callback_data=f"{CB_PREFIX}:set:quality:{q}",
        )
    kb.button(text="‹ Назад", callback_data=f"{CB_PREFIX}:menu")
    kb.adjust(3, 1)
    return kb.as_markup()


def model_menu(s: UserSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in MODELS:
        kb.button(text=_mark(m, s.model == m), callback_data=f"{CB_PREFIX}:set:model:{m}")
    kb.button(text="‹ Назад", callback_data=f"{CB_PREFIX}:menu")
    kb.adjust(1)
    return kb.as_markup()


def fidelity_menu(s: UserSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for f in FIDELITIES:
        kb.button(
            text=_mark(FIDELITY_LABELS[f], s.fidelity == f),
            callback_data=f"{CB_PREFIX}:set:fidelity:{f}",
        )
    kb.button(text="‹ Назад", callback_data=f"{CB_PREFIX}:menu")
    kb.adjust(2, 1)
    return kb.as_markup()


def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="‹ Назад", callback_data=f"{CB_PREFIX}:open:aspect")]
        ]
    )
