"""Точка входа: сборка и запуск бота в режиме polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import load_config
from app.db.database import Database
from app.handlers import router
from app.middlewares.access import AccessMiddleware
from app.middlewares.db_session import DbSessionMiddleware
from app.services.openai_image import OpenAIImageService

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    config = load_config()

    db = Database(config.db_path)
    await db.connect()

    image_service = OpenAIImageService(
        api_key=config.openai_api_key,
        model=config.openai_model,
        size=config.image_size,
        quality=config.image_quality,
    )

    bot = Bot(
        config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(db))
    dp.message.middleware(AccessMiddleware(config.owner_ids))
    dp.include_router(router)

    logger.info(
        "Старт бота | model=%s size=%s quality=%s | owners=%s",
        config.openai_model,
        config.image_size,
        config.image_quality,
        ", ".join(map(str, sorted(config.owner_ids))) or "ВСЕ",
    )

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, image_service=image_service)
    finally:
        await image_service.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановлено")
