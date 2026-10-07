"""Real translations through Google Translate (network required).

Assertions use stable substrings only - Google's exact wording changes
over time and must never be pinned. Deselect with --offline or -m "not online".
"""

import pytest

from helpers import call_with_retry

pytestmark = pytest.mark.online


async def test_translate_english_to_german(translator):
    result = await call_with_retry(lambda: translator.translate("Hello, world!", dest="de"))
    assert result.src == "en"
    assert result.dest == "de"
    assert result.origin == "Hello, world!"
    assert "hallo" in result.text.lower()
    assert result._response.status_code == 200


async def test_translate_with_explicit_source(translator):
    result = await call_with_retry(
        lambda: translator.translate("Guten Morgen", src="de", dest="en")
    )
    assert result.src == "de"
    assert result.dest == "en"
    assert "morning" in result.text.lower()


async def test_translate_destination_by_language_name(translator):
    result = await call_with_retry(
        lambda: translator.translate("Good morning", dest="german")
    )
    assert result.dest == "de"
    assert "morgen" in result.text.lower()


async def test_translate_batch_preserves_order(translator):
    texts = ["Hello", "Thank you", "Goodbye"]
    results = await call_with_retry(lambda: translator.translate(texts, dest="de"))
    assert isinstance(results, list)
    assert [item.origin for item in results] == texts
    assert "danke" in results[1].text.lower()
    assert all(item.text for item in results)


async def test_translate_non_latin_text(translator):
    result = await call_with_retry(lambda: translator.translate("你好，世界", dest="en"))
    assert result.src.lower() in {"zh-cn", "zh"}
    assert "hello" in result.text.lower()


async def test_translate_round_trip(translator):
    german = await call_with_retry(
        lambda: translator.translate("The weather is nice today.", dest="de")
    )
    back = await call_with_retry(
        lambda: translator.translate(german.text, src="de", dest="en")
    )
    assert "weather" in back.text.lower()
    assert "today" in back.text.lower()
