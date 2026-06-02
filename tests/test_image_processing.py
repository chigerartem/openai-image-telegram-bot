"""Тесты пост-обработки: обрезка под соотношение и подгон под точный размер."""

from __future__ import annotations

import io

from PIL import Image

from app.services.image_processing import crop_to_ratio, fit_to_size, to_png


def _png(width: int, height: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (120, 80, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _dims(data: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(data)).size


def test_crop_to_ratio_16_9_from_landscape() -> None:
    out = crop_to_ratio(_png(1536, 1024), 16, 9)
    w, h = _dims(out)
    assert w == 1536  # ширина сохраняется
    assert abs(w / h - 16 / 9) < 0.01


def test_crop_to_ratio_9_16_from_portrait() -> None:
    out = crop_to_ratio(_png(1024, 1536), 9, 16)
    w, h = _dims(out)
    assert h == 1536  # высота сохраняется
    assert abs(w / h - 9 / 16) < 0.01


def test_fit_to_size_exact_dimensions() -> None:
    out = fit_to_size(_png(1536, 1024), 1920, 1080)
    assert _dims(out) == (1920, 1080)


def test_to_png_converts_jpeg() -> None:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 20, 30)).save(buf, format="JPEG")
    out = to_png(buf.getvalue())
    assert Image.open(io.BytesIO(out)).format == "PNG"
