"""Тесты парсинга OWNER_IDS."""

from __future__ import annotations

from app.config import _parse_ids


def test_parse_ids_basic() -> None:
    assert _parse_ids("123,456") == frozenset({123, 456})


def test_parse_ids_with_spaces() -> None:
    assert _parse_ids("  123 ,  456 ") == frozenset({123, 456})


def test_parse_ids_empty() -> None:
    assert _parse_ids("") == frozenset()


def test_parse_ids_ignores_garbage() -> None:
    assert _parse_ids("123, abc, 456,") == frozenset({123, 456})


def test_parse_ids_single() -> None:
    assert _parse_ids("999") == frozenset({999})
