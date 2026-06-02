"""Пресеты генерации и модель пользовательских настроек.

Здесь живёт вся «таблица соответствий»: какие форматы/качества/модели доступны
и как выбранный пользователем формат превращается в параметры запроса к OpenAI
(нативный размер API + опциональная обрезка/подгон под точный размер на нашей стороне).
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Нативные размеры, которые принимает Images API для моделей gpt-image-* ---
SIZE_SQUARE = "1024x1024"
SIZE_LANDSCAPE = "1536x1024"  # ≈ 3:2
SIZE_PORTRAIT = "1024x1536"  # ≈ 2:3
SIZE_AUTO = "auto"

# Границы для «своего» разрешения (в пикселях).
CUSTOM_MIN = 256
CUSTOM_MAX = 4096


@dataclass(frozen=True, slots=True)
class Aspect:
    """Один пресет формата: подпись для кнопки и как его рендерить."""

    key: str
    label: str
    api_size: str
    crop: tuple[int, int] | None = None  # соотношение для обрезки, если нужно


# Порядок здесь = порядок кнопок в меню.
ASPECTS: dict[str, Aspect] = {
    "square": Aspect("square", "1:1 ⬜", SIZE_SQUARE),
    "landscape": Aspect("landscape", "3:2 🖼", SIZE_LANDSCAPE),
    "portrait": Aspect("portrait", "2:3 📱", SIZE_PORTRAIT),
    "wide": Aspect("wide", "16:9 🎬", SIZE_LANDSCAPE, crop=(16, 9)),
    "tall": Aspect("tall", "9:16 📲", SIZE_PORTRAIT, crop=(9, 16)),
    "auto": Aspect("auto", "Auto ✨", SIZE_AUTO),
}

QUALITIES: tuple[str, ...] = ("low", "medium", "high")
QUALITY_LABELS = {"low": "Низкое", "medium": "Среднее", "high": "Высокое"}

FIDELITIES: tuple[str, ...] = ("low", "high")
FIDELITY_LABELS = {"low": "Обычная", "high": "Высокая"}

MODELS: tuple[str, ...] = (
    "gpt-image-2",
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-1-mini",
)


@dataclass(frozen=True, slots=True)
class UserSettings:
    """Снимок настроек одного пользователя (то, что лежит в БД)."""

    aspect: str
    custom_w: int | None
    custom_h: int | None
    quality: str
    model: str
    fidelity: str

    def aspect_label(self) -> str:
        if self.aspect == "custom":
            if self.custom_w and self.custom_h:
                return f"{self.custom_w}×{self.custom_h} ✏️"
            return "Своё ✏️"
        preset = ASPECTS.get(self.aspect)
        return preset.label if preset else self.aspect

    def quality_label(self) -> str:
        return QUALITY_LABELS.get(self.quality, self.quality)

    def fidelity_label(self) -> str:
        return FIDELITY_LABELS.get(self.fidelity, self.fidelity)


@dataclass(frozen=True, slots=True)
class RenderPlan:
    """Как именно рендерить запрос: размер для API + что сделать с результатом."""

    api_size: str
    crop_ratio: tuple[int, int] | None  # обрезать под соотношение (cover-crop)
    exact_size: tuple[int, int] | None  # подогнать ровно под эти пиксели


def _nearest_native_size(width: int, height: int) -> str:
    """Подбирает нативный размер API, чей формат ближе всего к запрошенному."""
    target = width / height
    options = {SIZE_SQUARE: 1.0, SIZE_LANDSCAPE: 1.5, SIZE_PORTRAIT: 2 / 3}
    return min(options, key=lambda size: abs(options[size] - target))


def plan_render(settings: UserSettings) -> RenderPlan:
    """Превращает выбор пользователя в конкретный план рендера."""
    if settings.aspect == "custom" and settings.custom_w and settings.custom_h:
        w, h = settings.custom_w, settings.custom_h
        return RenderPlan(_nearest_native_size(w, h), (w, h), (w, h))

    preset = ASPECTS.get(settings.aspect, ASPECTS["square"])
    return RenderPlan(preset.api_size, preset.crop, None)


def parse_custom_size(raw: str) -> tuple[int, int] | None:
    """«1920x1080» / «1920×1080» / «1920 1080» → (1920, 1080). Иначе None."""
    cleaned = raw.lower().replace("×", "x").replace("*", "x").replace(":", "x")
    for sep in ("x", " "):
        if sep in cleaned:
            parts = [p.strip() for p in cleaned.split(sep) if p.strip()]
            if len(parts) != 2:
                continue
            try:
                w, h = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if CUSTOM_MIN <= w <= CUSTOM_MAX and CUSTOM_MIN <= h <= CUSTOM_MAX:
                return w, h
            return None
    return None
