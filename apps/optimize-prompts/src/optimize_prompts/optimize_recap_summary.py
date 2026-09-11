"""Prompt Forge workflow for optimizing the Recap Summary prompt."""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from prompt_model import optimize_prompt
from prompt_model.config import EvalCase, LiteLLMConfig, OptimizerConfig
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .recap_summary_metrics import build_recap_summary_metrics
from .recap_summary_scorer import RecapSummaryGatedScorer
from .winner_output import checkpoint_callback, report_interruption, resolve_seed_prompt, save_winner


class RecapSummaryOptimizerSettings(BaseModel):
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


class RecapSummarySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_llm: LiteLLMConfig
    actor_llm: LiteLLMConfig
    judge_llm: LiteLLMConfig
    optimizer: RecapSummaryOptimizerSettings
    alignment_threshold: float = 0.95


def _load_eval_cases(inputs_directory: Path) -> list[EvalCase]:
    input_paths = sorted(inputs_directory.glob("*.txt"))
    if not input_paths:
        raise ValueError(f"No evaluation inputs found in {inputs_directory}.")
    return [EvalCase(input=path.read_text(encoding="utf-8"), source_path=path.name) for path in input_paths]


def _load_settings(path: Path) -> RecapSummarySettings:
    if not path.is_file():
        raise ValueError(f"Recap Summary settings not found at {path}.")
    with path.open(encoding="utf-8") as stream:
        return RecapSummarySettings.model_validate(yaml.safe_load(stream) or {})


def optimize_recap_summary(prompt_directory: Path, console: Console, *, run: bool = False, resume: bool = False) -> None:
    seed_prompt_path = prompt_directory / "seed_prompt.txt"
    inputs_directory = prompt_directory / "inputs"
    output_directory = prompt_directory / "outputs"
    if not seed_prompt_path.is_file():
        raise ValueError(f"Seed prompt not found at {seed_prompt_path}.")
    if not inputs_directory.is_dir():
        raise ValueError(f"Evaluation inputs directory not found at {inputs_directory}.")

    settings = _load_settings(prompt_directory / "settings.yaml")
    config = OptimizerConfig(
        seed_prompt=resolve_seed_prompt(seed_prompt_path, output_directory, resume=resume, console=console),
        eval_cases=_load_eval_cases(inputs_directory),
        target_llm=settings.target_llm,
        actor_llm=settings.actor_llm,
        judge_llm=settings.judge_llm,
        **settings.optimizer.model_dump(),
    )
    metrics = build_recap_summary_metrics(
        judge_llm=config.judge_llm,
        coverage_question_directory=prompt_directory / "coverage_questions",
    )
    scorer = RecapSummaryGatedScorer(alignment_threshold=settings.alignment_threshold)
    console.print(
        Panel(
            f"Prompt Model configuration created with {len(config.eval_cases)} evaluation cases and {len(metrics)} metrics.",
            title="Recap Summary Optimization",
            border_style="cyan",
        )
    )
    console.print(Syntax(config.model_dump_json(indent=2), "json"))
    if not run:
        return
    try:
        result = asyncio.run(
            optimize_prompt(
                config=config,
                metrics=metrics,
                scorer=scorer,
                on_checkpoint=lambda prompt: checkpoint_callback(output_directory, prompt),
            )
        )
    except BaseException as exc:
        report_interruption(exc, output_directory, console, title="Recap Summary Optimization")
        raise
    prompt_path = save_winner(
        output_directory,
        result.best_prompt,
        {"mode": "full_corpus", "result": result.model_dump(mode="json")},
    )
    console.print(
        Panel(
            f"Best score: {result.best_score:.4f}\nWinner saved to: {prompt_path}",
            title="Recap Summary Optimization Complete",
            border_style="cyan",
        )
    )
