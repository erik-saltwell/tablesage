from __future__ import annotations

import sys
import types
from importlib import import_module
from typing import Any, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.mark.anyio
async def test_punctuate_text_skips_empty_strings(monkeypatch: MonkeyPatch) -> None:
    class FakePunctuationModel:
        received_texts: list[str] | None = None

        @classmethod
        def from_pretrained(cls, model_name: str) -> type[FakePunctuationModel]:
            assert model_name == "pcs_en"
            return cls

        @classmethod
        def infer(cls, texts: list[str], apply_sbd: bool) -> list[str]:
            assert apply_sbd is False
            cls.received_texts = texts
            return ["Hello world.", "Bye now."]

    def clean_text_for_evaluation(text: str, do_mathspell: bool) -> str:
        assert do_mathspell is False
        return "" if text == "..." else text.strip()

    fake_text_cleaner = cast(Any, types.ModuleType("tablesage_model.tools.text_cleaner"))
    fake_text_cleaner.clean_text_for_evaluation = clean_text_for_evaluation
    monkeypatch.setitem(sys.modules, "tablesage_model.tools.text_cleaner", fake_text_cleaner)

    fake_punctuator_models = cast(Any, types.ModuleType("punctuators.models"))
    fake_punctuator_models.PunctCapSegModelONNX = FakePunctuationModel
    monkeypatch.setitem(sys.modules, "punctuators.models", fake_punctuator_models)

    monkeypatch.delitem(sys.modules, "tablesage_model.tools.punctuation", raising=False)
    punctuation = import_module("tablesage_model.tools.punctuation")

    result = await punctuation.punctuate_text(["hello world", "", "...", "bye now"])

    assert FakePunctuationModel.received_texts == ["hello world", "bye now"]
    assert result == ["Hello world.", "", "...", "Bye now."]
