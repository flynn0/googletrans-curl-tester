"""Real language detection through Google Translate (network required)."""

import pytest

from helpers import call_with_retry

pytestmark = pytest.mark.online


async def test_detect_french(translator):
    result = await call_with_retry(lambda: translator.detect("Bonjour tout le monde"))
    assert result.lang == "fr"
    assert 0.0 <= result.confidence <= 1.0


async def test_detect_japanese(translator):
    result = await call_with_retry(lambda: translator.detect("こんにちは世界"))
    assert result.lang == "ja"


async def test_detect_batch(translator):
    texts = ["Bonjour tout le monde", "こんにちは世界"]
    results = await call_with_retry(lambda: translator.detect(texts))
    assert [item.lang for item in results] == ["fr", "ja"]
