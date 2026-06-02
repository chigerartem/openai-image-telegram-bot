"""Пост-обработка PNG на нашей стороне: cover-crop под соотношение и подгон под точный размер.

Нужна потому, что Images API отдаёт только нативные форматы (1:1, 3:2, 2:3).
Чтобы получить 16:9 или произвольное разрешение, обрезаем/масштабируем результат сами.
"""

from __future__ import annotations

import io

from PIL import Image


def _load(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def _encode(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _cover_box(src_w: int, src_h: int, ratio_w: int, ratio_h: int) -> tuple[int, int, int, int]:
    """Центрированный прямоугольник внутри src с заданным соотношением (режим cover)."""
    target = ratio_w / ratio_h
    if src_w / src_h > target:
        # Источник шире нужного — режем по бокам.
        new_w = round(src_h * target)
        left = (src_w - new_w) // 2
        return left, 0, left + new_w, src_h
    # Источник выше нужного — режем сверху/снизу.
    new_h = round(src_w / target)
    top = (src_h - new_h) // 2
    return 0, top, src_w, top + new_h


def to_png(data: bytes) -> bytes:
    """Перекодирует любую картинку (JPEG из Telegram и т.п.) в PNG."""
    return _encode(_load(data))


def crop_to_ratio(data: bytes, ratio_w: int, ratio_h: int) -> bytes:
    """Центрированная обрезка под соотношение сторон (без масштабирования)."""
    image = _load(data)
    box = _cover_box(image.width, image.height, ratio_w, ratio_h)
    return _encode(image.crop(box))


def fit_to_size(data: bytes, width: int, height: int) -> bytes:
    """Cover-crop под соотношение width:height, затем масштаб ровно до width×height."""
    image = _load(data)
    box = _cover_box(image.width, image.height, width, height)
    cropped = image.crop(box)
    resized = cropped.resize((width, height), Image.LANCZOS)
    return _encode(resized)
