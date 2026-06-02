"""Тесты разрешения форматов и парсинга своего размера."""

from __future__ import annotations

from app.presets import (
    SIZE_LANDSCAPE,
    SIZE_PORTRAIT,
    SIZE_SQUARE,
    UserSettings,
    parse_custom_size,
    plan_render,
)


def _settings(aspect: str, w: int | None = None, h: int | None = None) -> UserSettings:
    return UserSettings(
        aspect=aspect, custom_w=w, custom_h=h,
        quality="high", model="gpt-image-2", fidelity="low",
    )


def test_plan_native_sizes_have_no_postprocessing() -> None:
    for aspect, size in (
        ("square", SIZE_SQUARE),
        ("landscape", SIZE_LANDSCAPE),
        ("portrait", SIZE_PORTRAIT),
    ):
        plan = plan_render(_settings(aspect))
        assert plan.api_size == size
        assert plan.crop_ratio is None
        assert plan.exact_size is None


def test_plan_wide_crops_landscape() -> None:
    plan = plan_render(_settings("wide"))
    assert plan.api_size == SIZE_LANDSCAPE
    assert plan.crop_ratio == (16, 9)
    assert plan.exact_size is None


def test_plan_tall_crops_portrait() -> None:
    plan = plan_render(_settings("tall"))
    assert plan.api_size == SIZE_PORTRAIT
    assert plan.crop_ratio == (9, 16)


def test_plan_custom_picks_nearest_native_and_exact_size() -> None:
    plan = plan_render(_settings("custom", 1920, 1080))  # широкий → landscape
    assert plan.api_size == SIZE_LANDSCAPE
    assert plan.exact_size == (1920, 1080)

    plan = plan_render(_settings("custom", 1080, 1920))  # высокий → portrait
    assert plan.api_size == SIZE_PORTRAIT
    assert plan.exact_size == (1080, 1920)


def test_plan_custom_without_dimensions_falls_back() -> None:
    plan = plan_render(_settings("custom"))  # нет размеров → дефолт
    assert plan.api_size == SIZE_SQUARE


def test_parse_custom_size_variants() -> None:
    assert parse_custom_size("1920x1080") == (1920, 1080)
    assert parse_custom_size("1920×1080") == (1920, 1080)
    assert parse_custom_size("1920 1080") == (1920, 1080)
    assert parse_custom_size("800*600") == (800, 600)


def test_parse_custom_size_rejects_out_of_range_and_garbage() -> None:
    assert parse_custom_size("100x100") is None  # ниже минимума
    assert parse_custom_size("9000x9000") is None  # выше максимума
    assert parse_custom_size("hello") is None
    assert parse_custom_size("1024") is None
    assert parse_custom_size("1x2x3") is None
