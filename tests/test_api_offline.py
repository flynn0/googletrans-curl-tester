"""Offline API checks - no network requests are made."""

import pytest

from googletrans import LANGCODES, LANGUAGES, Translator
from googletrans.models import Detected, Translated


def test_submodules_are_importable():
    from googletrans import client, constants, gtoken, models, urls, utils  # noqa: F401


def test_language_tables_are_populated():
    assert len(LANGUAGES) > 100
    assert LANGUAGES["en"] == "english"
    assert LANGUAGES["de"] == "german"
    assert LANGCODES["english"] == "en"
    assert LANGCODES["german"] == "de"


async def test_translator_supports_async_context_manager():
    async with Translator() as instance:
        assert isinstance(instance, Translator)


async def test_translate_rejects_invalid_destination(translator):
    with pytest.raises(ValueError, match="invalid destination language"):
        await translator.translate("Hello", dest="not-a-language")


async def test_translate_rejects_invalid_source(translator):
    with pytest.raises(ValueError, match="invalid source language"):
        await translator.translate("Hello", src="not-a-language")


def test_translated_model_contract():
    result = Translated(
        src="en", dest="de", origin="Hello", text="Hallo", pronunciation="Hallo"
    )
    assert (result.src, result.dest, result.origin, result.text) == (
        "en",
        "de",
        "Hello",
        "Hallo",
    )
    assert "Hallo" in str(result)


def test_detected_model_contract():
    result = Detected(lang="de", confidence=0.98)
    assert result.lang == "de"
    assert 0.0 <= result.confidence <= 1.0
    assert "de" in str(result)
