"""Сервис генерации изображений через OpenAI Images API."""

from __future__ import annotations

import base64
import logging

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Не удалось сгенерировать изображение (текст — уже человекочитаемый)."""


class OpenAIImageService:
    """Тонкая обёртка над AsyncOpenAI: промпт → PNG-байты."""

    def __init__(self, api_key: str, model: str, size: str, quality: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._size = size
        self._quality = quality

    @property
    def model(self) -> str:
        return self._model

    @property
    def size(self) -> str:
        return self._size

    @property
    def quality(self) -> str:
        return self._quality

    async def generate(self, prompt: str) -> bytes:
        """Генерирует одно изображение и возвращает его как PNG-байты."""
        try:
            result = await self._client.images.generate(
                model=self._model,
                prompt=prompt,
                size=self._size,
                quality=self._quality,
                n=1,
            )
        except OpenAIError as exc:
            logger.warning("OpenAI image generation failed: %s", exc)
            raise ImageGenerationError(_human_error(exc)) from exc

        if not result.data or not result.data[0].b64_json:
            raise ImageGenerationError("OpenAI вернул пустой ответ")

        # Модели gpt-image-* всегда отдают изображение в base64, не URL.
        return base64.b64decode(result.data[0].b64_json)

    async def close(self) -> None:
        await self._client.close()


def _human_error(exc: OpenAIError) -> str:
    """Превращает техническую ошибку OpenAI в понятное пользователю сообщение."""
    text = str(exc)
    low = text.lower()
    if any(k in low for k in ("content_policy", "safety", "moderation")):
        return "запрос отклонён модерацией OpenAI — переформулируй описание"
    if any(k in low for k in ("billing", "quota", "insufficient")):
        return "закончились кредиты OpenAI или превышен лимит запросов"
    if any(k in low for k in ("verify", "verification", "must be verified")):
        return (
            "у аккаунта нет доступа к этой модели — нужна верификация организации "
            "OpenAI либо смени OPENAI_MODEL в .env на gpt-image-1-mini"
        )
    return f"ошибка OpenAI: {text}"
