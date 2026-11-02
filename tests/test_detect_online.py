"""Real language detection through Google Translate (network required)."""

import pytest

from helpers import call_sync_with_retry, call_with_retry

pytestmark = pytest.mark.online


async def test_detect_french(translator):
    result = await call_with_retry(lambda: translator.detect("Bonjour tout le monde"))
    assert result.lang == "fr"
    assert 0.0 <= result.confidence <= 1.0


def test_sync_detect_french(sync_translator):
    result = call_sync_with_retry(
        lambda: sync_translator.detect("Bonjour tout le monde")
    )
    assert result.lang == "fr"
    assert 0.0 <= result.confidence <= 1.0


async def test_detect_japanese(translator):
    result = await call_with_retry(lambda: translator.detect("こんにちは世界"))
    assert result.lang == "ja"


async def test_detect_batch(translator):
    texts = ["Bonjour tout le monde", "こんにちは世界"]
    results = await call_with_retry(lambda: translator.detect(texts))
    assert [item.lang for item in results] == ["fr", "ja"]


def test_sync_detect_batch(sync_translator):
    texts = ["Bonjour tout le monde", "こんにちは世界"]
    results = call_sync_with_retry(lambda: sync_translator.detect(texts))
    assert [item.lang for item in results] == ["fr", "ja"]


def test_translator_detect_sync_method():
    from googletrans import Translator

    translator = Translator()
    result = call_sync_with_retry(
        lambda: translator.detect_sync("Bonjour tout le monde")
    )
    assert result.lang == "fr"
