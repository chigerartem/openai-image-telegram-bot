"""Сервис генерации изображений через OpenAI Images API.

Поддерживает два режима:
  - generate(): текст → изображение;
  - edit():     текст + референс-картинка(и) → изображение.
Параметры (модель, размер, качество) передаются на каждый запрос, чтобы у каждого
пользователя могли быть свои настройки.
"""

from __future__ import annotations

import base64
import logging

from openai import AsyncOpenAI, OpenAIError

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Не удалось сгенерировать изображение (текст — уже человекочитаемый)."""


class OpenAIImageService:
    """Тонкая обёртка над AsyncOpenAI: промпт (+ референс) → PNG-байты."""

    def __init__(self, api_key: str, default_model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._default_model = default_model

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate(self, prompt: str, *, model: str, size: str, quality: str) -> bytes:
        """Текст → одно изображение (PNG-байты)."""
        try:
            result = await self._client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
        except OpenAIError as exc:
            logger.warning("OpenAI image generate failed: %s", exc)
            raise ImageGenerationError(_human_error(exc)) from exc

        return _extract_png(result)

    async def edit(
        self,
        prompt: str,
        images: list[bytes],
        *,
        model: str,
        size: str,
        quality: str,
        input_fidelity: str,
    ) -> bytes:
        """Текст + референс(ы) → одно изображение (PNG-байты)."""
        files = [("reference.png", data, "image/png") for data in images]
        try:
            result = await self._client.images.edit(
                model=model,
                prompt=prompt,
                image=files if len(files) > 1 else files[0],
                size=size,
                quality=quality,
                input_fidelity=input_fidelity,
                n=1,
            )
        except OpenAIError as exc:
            logger.warning("OpenAI image edit failed: %s", exc)
            raise ImageGenerationError(_human_error(exc)) from exc

        return _extract_png(result)

    async def close(self) -> None:
        await self._client.close()


def _extract_png(result: object) -> bytes:
    """Достаёт PNG-байты из ответа API (модели gpt-image-* отдают base64, не URL)."""
    data = getattr(result, "data", None)
    if not data or not getattr(data[0], "b64_json", None):
        raise ImageGenerationError("OpenAI вернул пустой ответ")
    return base64.b64decode(data[0].b64_json)


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
            "OpenAI либо выбери модель gpt-image-1-mini в /settings"
        )
    return f"ошибка OpenAI: {text}"
