from __future__ import annotations

from pathlib import Path

import yaml

from .bundle import RESPONSE_SCHEMA_FILENAME, EvaluationBundle

_PLUGIN_MODULE = "tablesage_prompt_metrics"


def _settings(bundle: EvaluationBundle, *, smoke: bool) -> dict[str, object]:
    optimization: dict[str, object]
    if smoke:
        optimization = {
            "iterations": 1,
            "early_stop_patience": 1,
            "max_llm_concurrency": 1,
            "top_k_per_iteration": 1,
            "floor": 1,
            "ucb_budget": 0,
            "seed_warmup_pulls": 1,
            "max_children_per_parent": 1,
            "error_budget": 0,
            "seed": 1,
        }
    else:
        optimization = {
            "iterations": 8,
            "early_stop_patience": 3,
            "max_llm_concurrency": 4,
            "top_k_per_iteration": 3,
            "floor": 2,
            "ucb_budget": 20,
            "seed_warmup_pulls": 2,
            "max_children_per_parent": 3,
            "min_improvement_delta": 0.005,
            "exploration_bonus": 1.0,
            "error_budget": 0,
            "seed": 1,
        }
    return {
        "target_llm": {"model": "anthropic/claude-fable-5.1"},
        "actor_llm": {"model": "anthropic/claude-sonnet-5", "temperature": 0.5},
        "judge_llm": {"model": "anthropic/claude-sonnet-5", "temperature": 0.0},
        "evaluation": {
            "case_loader": f"{_PLUGIN_MODULE}:build_cases",
            "metric_factory": f"{_PLUGIN_MODULE}:build_metrics",
            "scorer_factory": f"{_PLUGIN_MODULE}:build_scorer",
            "observer_factory": f"{_PLUGIN_MODULE}:build_observer",
            "plugin_config": {"bundle": ".", "report_dir": "./report"},
        },
        "target_response_schema": {"path": f"./{RESPONSE_SCHEMA_FILENAME}", "name": "LedgerGenerationResponse"},
        **optimization,
    }


def write_profiles(bundle: EvaluationBundle) -> tuple[Path, Path]:
    smoke_path: Path = bundle.root / "prompt-forge-smoke.yaml"
    full_path: Path = bundle.root / "prompt-forge-full.yaml"
    smoke_path.write_text(yaml.safe_dump(_settings(bundle, smoke=True), sort_keys=False), encoding="utf-8")
    full_path.write_text(yaml.safe_dump(_settings(bundle, smoke=False), sort_keys=False), encoding="utf-8")
    return smoke_path, full_path
