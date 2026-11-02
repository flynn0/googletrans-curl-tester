"""Offline API checks - no network requests are made."""

import pytest

from googletrans import (
    LANGCODES,
    LANGUAGES,
    RateLimitError,
    SyncTranslator,
    TranslationError,
    Translator,
)
from googletrans.client import _normalize_lang
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


def test_sync_translator_supports_context_manager():
    with SyncTranslator() as instance:
        assert isinstance(instance, SyncTranslator)


async def test_translate_rejects_invalid_destination(translator):
    with pytest.raises(ValueError, match="invalid destination language"):
        await translator.translate("Hello", dest="not-a-language")


async def test_translate_rejects_invalid_source(translator):
    with pytest.raises(ValueError, match="invalid source language"):
        await translator.translate("Hello", src="not-a-language")


def test_sync_translate_rejects_invalid_destination(sync_translator):
    with pytest.raises(ValueError, match="invalid destination language"):
        sync_translator.translate("Hello", dest="not-a-language")


def test_sync_translate_rejects_invalid_source(sync_translator):
    with pytest.raises(ValueError, match="invalid source language"):
        sync_translator.translate("Hello", src="not-a-language")


def test_translator_rejects_invalid_transport():
    with pytest.raises(ValueError, match="Invalid transport"):
        Translator(transport="invalid_transport")


def test_sync_translator_rejects_invalid_transport():
    with pytest.raises(ValueError, match="Invalid transport"):
        SyncTranslator(transport="invalid_transport")


def test_language_normalization():
    assert _normalize_lang("en_US") == "en"
    assert _normalize_lang("zh_CN") == "zh-cn"
    assert _normalize_lang("DE") == "de"


def test_exception_hierarchy():
    assert issubclass(RateLimitError, TranslationError)
    err = TranslationError("network error", status_code=500)
    assert err.status_code == 500
    assert "network error" in str(err)


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
