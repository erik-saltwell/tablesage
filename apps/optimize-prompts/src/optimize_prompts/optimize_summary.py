"""Prompt Forge workflow for optimizing the OptimEyes Summary prompt."""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from prompt_model import optimize_prompt
from prompt_model.config import EvalCase, LiteLLMConfig, OptimizerConfig
from prompt_model.scorers import WeightedMeanScorer
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .summary_metrics import build_summary_metrics


class SummaryOptimizerSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iterations: int
    top_k_per_iteration: int
    floor: int
    ucb_budget: int
    seed_warmup_pulls: int
    max_children_per_parent: int
    early_stop_patience: int
    max_llm_concurrency: int
    error_budget: int
    seed: int | None


class SummarySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_llm: LiteLLMConfig
    actor_llm: LiteLLMConfig
    judge_llm: LiteLLMConfig
    optimizer: SummaryOptimizerSettings
    metric_weights: dict[str, float]


def _load_eval_cases(inputs_directory: Path) -> list[EvalCase]:
    input_paths = sorted(inputs_directory.glob("*.txt"))
    if not input_paths:
        raise ValueError(f"No evaluation inputs found in {inputs_directory}.")
    return [EvalCase(input=input_path.read_text(encoding="utf-8"), source_path=input_path.name) for input_path in input_paths]


def _load_settings(path: Path) -> SummarySettings:
    if not path.is_file():
        raise ValueError(f"Summary settings not found at {path}.")
    with path.open(encoding="utf-8") as stream:
        return SummarySettings.model_validate(yaml.safe_load(stream) or {})


def _build_summary_config(seed_prompt: str, eval_cases: list[EvalCase], settings: SummarySettings) -> OptimizerConfig:
    return OptimizerConfig(
        seed_prompt=seed_prompt,
        eval_cases=eval_cases,
        target_llm=settings.target_llm,
        actor_llm=settings.actor_llm,
        judge_llm=settings.judge_llm,
        **settings.optimizer.model_dump(),
    )


def optimize_summary(prompt_directory: Path, console: Console, *, run: bool = False) -> None:
    seed_prompt_path = prompt_directory / "seed_prompt.txt"
    inputs_directory = prompt_directory / "inputs"
    if not seed_prompt_path.is_file():
        raise ValueError(f"Seed prompt not found at {seed_prompt_path}.")
    if not inputs_directory.is_dir():
        raise ValueError(f"Input directory not found at {inputs_directory}.")

    settings = _load_settings(prompt_directory / "settings.yaml")
    config = _build_summary_config(seed_prompt_path.read_text(encoding="utf-8"), _load_eval_cases(inputs_directory), settings)
    metrics = build_summary_metrics(
        judge_llm=config.judge_llm,
        coverage_question_directory=prompt_directory / "coverage_questions",
    )
    scorer = WeightedMeanScorer(settings.metric_weights)

    console.print(
        Panel(
            f"Prompt Model configuration created with {len(config.eval_cases)} evaluation cases and {len(metrics)} metrics.",
            title="Summary Optimization",
            border_style="cyan",
        )
    )
    console.print(Syntax(config.model_dump_json(indent=2), "json"))
    if not run:
        return

    result = asyncio.run(optimize_prompt(config=config, metrics=metrics, scorer=scorer))
    console.print(Panel(f"Best score: {result.best_score:.4f}", title="Summary Optimization Complete", border_style="green"))
