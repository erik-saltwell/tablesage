from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from prompt_model import Metric
from prompt_model.config import EvalCase, LiteLLMConfig

from .bundle import EvaluationBundle
from .metrics import CompletenessMetric, ConcisionMetric, ExclusionMetric, HallucinationMetric, SchemaCorrectnessMetric
from .observer import LedgerRunObserver
from .scoring import LedgerScorer


def _value(source: object, name: str) -> object | None:
    if isinstance(source, Mapping):
        mapping: Mapping[str, object] = cast(Mapping[str, object], source)
        return mapping.get(name)
    return getattr(source, name, None)


def _settings_dir(context: object) -> Path:
    value: object | None = _value(context, "settings_dir")
    if value is None:
        return Path.cwd()
    if not isinstance(value, str | Path):
        raise ValueError("Prompt Forge plugin context settings_dir must be a path.")
    return Path(value).resolve()


def _bundle(context: object, config: Mapping[str, object]) -> EvaluationBundle:
    raw: object | None = config.get("bundle")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("plugin_config.bundle must be a non-empty path string.")
    path: Path = Path(raw)
    if not path.is_absolute():
        path = _settings_dir(context) / path
    return EvaluationBundle(path)


def _judge_llm(context: object) -> LiteLLMConfig:
    value: object | None = _value(context, "judge_llm")
    if isinstance(value, LiteLLMConfig):
        return value
    if isinstance(value, Mapping):
        return LiteLLMConfig.model_validate(value)
    raise ValueError("Prompt Forge plugin context must supply judge_llm.")


def build_cases(context: object, config: Mapping[str, object]) -> list[EvalCase]:
    bundle: EvaluationBundle = _bundle(context, config)
    ground_truth: str = json.dumps([question.model_dump(mode="json") for question in bundle.questions], ensure_ascii=False)
    return [EvalCase(input=bundle.user_prompt, ground_truth=ground_truth, retrieval_context=[bundle.transcript])]


def build_metrics(context: object, config: Mapping[str, object]) -> list[Metric]:
    bundle: EvaluationBundle = _bundle(context, config)
    judge_llm: LiteLLMConfig = _judge_llm(context)
    return [
        SchemaCorrectnessMetric(bundle.response_schema),
        HallucinationMetric(bundle.transcript, judge_llm),
        CompletenessMetric(bundle.questions, judge_llm),
        ExclusionMetric(kind="table_talk", judge_llm=judge_llm),
        ExclusionMetric(kind="mechanics", judge_llm=judge_llm),
        ConcisionMetric(bundle.transcript, judge_llm),
    ]


def build_scorer(context: object, config: Mapping[str, object]) -> LedgerScorer:
    _bundle(context, config)
    return LedgerScorer()


def build_observer(context: object, config: Mapping[str, object]) -> LedgerRunObserver:
    raw: object = config.get("report_dir", "./prompt-forge-report")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("plugin_config.report_dir must be a non-empty path string.")
    path: Path = Path(raw)
    if not path.is_absolute():
        path = _settings_dir(context) / path
    return LedgerRunObserver(path)
