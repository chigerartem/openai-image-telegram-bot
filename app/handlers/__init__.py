"""Агрегирующий router: подключает хендлеры в правильном порядке."""

from __future__ import annotations

from aiogram import Router

from app.handlers import commands, generate

router = Router()
router.include_router(commands.router)
router.include_router(generate.router)

__all__ = ["router"]
