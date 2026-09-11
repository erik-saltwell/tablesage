"""Prompt Forge workflow for optimizing transcript sectioning."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import yaml
from prompt_model import MetricResult, optimize_prompt
from prompt_model._llm.call import acomplete
from prompt_model.config import EvalCase, LiteLLMConfig, OptimizerConfig, TargetResponseSchema
from prompt_model.scorers import WeightedMeanScorer
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from tablesage_application.session_pipeline.transcript_sections import TranscriptSectionsGenerationResponse

from .sectioning_metrics import TranscriptSectioningMetric
from .winner_output import checkpoint_callback, report_interruption, resolve_seed_prompt, save_winner


class SectioningOptimizerSettings(BaseModel):
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


class SectioningSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_llm: LiteLLMConfig
    actor_llm: LiteLLMConfig
    judge_llm: LiteLLMConfig
    optimizer: SectioningOptimizerSettings
    metric_weights: dict[str, float]


def _load_eval_cases(inputs_directory: Path, ground_truth_directory: Path) -> list[EvalCase]:
    input_paths = sorted(inputs_directory.glob("*.txt"))
    if not input_paths:
        raise ValueError(f"No evaluation inputs found in {inputs_directory}.")

    cases: list[EvalCase] = []
    for input_path in input_paths:
        ground_truth_path = ground_truth_directory / f"{input_path.stem}.json"
        if not ground_truth_path.is_file():
            raise ValueError(f"Golden transcript sections not found for {input_path.name}: expected {ground_truth_path}.")
        cases.append(
            EvalCase(
                input=input_path.read_text(encoding="utf-8"),
                ground_truth=ground_truth_path.read_text(encoding="utf-8"),
                source_path=input_path.name,
            )
        )
    return cases


def _load_settings(path: Path) -> SectioningSettings:
    if not path.is_file():
        raise ValueError(f"Transcript-sectioning settings not found at {path}.")
    with path.open(encoding="utf-8") as stream:
        return SectioningSettings.model_validate(yaml.safe_load(stream) or {})


def _build_config(seed_prompt: str, eval_cases: list[EvalCase], settings: SectioningSettings) -> OptimizerConfig:
    return OptimizerConfig(
        seed_prompt=seed_prompt,
        eval_cases=eval_cases,
        target_llm=settings.target_llm,
        actor_llm=settings.actor_llm,
        judge_llm=settings.judge_llm,
        target_response_schema=TargetResponseSchema(
            name="transcript_sections_generation_response",
            json_schema=TranscriptSectionsGenerationResponse.model_json_schema(),
        ),
        **settings.optimizer.model_dump(),
    )


async def _score_holdout(prompt: str, case: EvalCase, settings: SectioningSettings) -> MetricResult:
    output = await acomplete(
        prompt,
        case.input,
        settings.target_llm,
        target_schema=TargetResponseSchema(
            name="transcript_sections_generation_response",
            json_schema=TranscriptSectionsGenerationResponse.model_json_schema(),
        ),
    )
    assert isinstance(output, str)
    return await TranscriptSectioningMetric().evaluate(prompt, case, output)


async def _run_cross_validation(
    seed_prompt: str,
    cases: list[EvalCase],
    settings: SectioningSettings,
    output_directory: Path,
    console: Console,
) -> None:
    if len(cases) < 2:
        raise ValueError("Transcript-sectioning cross-validation requires at least two evaluation cases.")
    scorer = WeightedMeanScorer(settings.metric_weights)
    winner: tuple[str, float, dict[str, Any]] | None = None
    for held_out in cases:
        training_cases = [case for case in cases if case != held_out]
        config = _build_config(seed_prompt, training_cases, settings)
        try:
            result = await optimize_prompt(
                config=config,
                metrics=[TranscriptSectioningMetric()],
                scorer=scorer,
                on_checkpoint=lambda prompt: checkpoint_callback(output_directory, prompt),
            )
        except BaseException as exc:
            report_interruption(exc, output_directory, console, title="Transcript Sectioning Cross-validation")
            raise
        holdout_result = await _score_holdout(result.best_prompt, held_out, settings)
        metadata = {
            "mode": "cross_validation",
            "training_cases": [case.source_path for case in training_cases],
            "held_out_case": held_out.source_path,
            "training_result": result.model_dump(mode="json"),
            "held_out_result": holdout_result.model_dump(mode="json"),
        }
        if winner is None or holdout_result.score > winner[1]:
            winner = (result.best_prompt, holdout_result.score, metadata)
        console.print(
            Panel(
                f"Training cases: {', '.join(case.source_path or '<unknown>' for case in training_cases)}\n"
                f"Training best score: {result.best_score:.4f}\n"
                f"Held-out case: {held_out.source_path or '<unknown>'}\n"
                f"Held-out score: {holdout_result.score:.4f}\n"
                f"{holdout_result.assessment}",
                title="Transcript Sectioning Cross-validation Fold",
                border_style="cyan",
            )
        )
    assert winner is not None
    prompt_path = save_winner(output_directory, winner[0], winner[2])
    console.print(f"Cross-validation winner saved to {prompt_path}.")


async def _run_group_holdout(
    seed_prompt: str,
    cases: list[EvalCase],
    settings: SectioningSettings,
    output_directory: Path,
    holdout_prefix: str,
    console: Console,
) -> None:
    held_out = [case for case in cases if (case.source_path or "").startswith(holdout_prefix)]
    training = [case for case in cases if case not in held_out]
    if not held_out:
        raise ValueError(f"No evaluation cases matched holdout prefix {holdout_prefix!r}.")
    if not training:
        raise ValueError("Group holdout requires at least one training case outside the holdout prefix.")

    scorer = WeightedMeanScorer(settings.metric_weights)
    config = _build_config(seed_prompt, training, settings)
    try:
        result = await optimize_prompt(
            config=config,
            metrics=[TranscriptSectioningMetric()],
            scorer=scorer,
            on_checkpoint=lambda prompt: checkpoint_callback(output_directory, prompt),
        )
    except BaseException as exc:
        report_interruption(exc, output_directory, console, title="Transcript Sectioning Group Holdout")
        raise
    holdout_results = [await _score_holdout(result.best_prompt, case, settings) for case in held_out]
    holdout_score = sum(item.score for item in holdout_results) / len(holdout_results)
    metadata = {
        "mode": "group_holdout",
        "holdout_prefix": holdout_prefix,
        "training_cases": [case.source_path for case in training],
        "held_out_cases": [case.source_path for case in held_out],
        "training_result": result.model_dump(mode="json"),
        "held_out_results": [item.model_dump(mode="json") for item in holdout_results],
        "held_out_mean_score": holdout_score,
    }
    prompt_path = save_winner(output_directory, result.best_prompt, metadata)
    console.print(
        Panel(
            f"Training cases: {len(training)}\n"
            f"Held-out cases: {len(held_out)}\n"
            f"Held-out mean score: {holdout_score:.4f}\n"
            f"Winner saved to: {prompt_path}",
            title="Transcript Sectioning Group Holdout",
            border_style="cyan",
        )
    )


def optimize_section_transcript(
    prompt_directory: Path,
    console: Console,
    *,
    run: bool = False,
    resume: bool = False,
    cross_validate: bool = False,
    holdout_prefix: str | None = None,
) -> None:
    seed_prompt_path = prompt_directory / "seed_prompt.txt"
    inputs_directory = prompt_directory / "inputs"
    ground_truth_directory = prompt_directory / "ground_truth"
    output_directory = prompt_directory / "outputs"
    if not seed_prompt_path.is_file():
        raise ValueError(f"Seed prompt not found at {seed_prompt_path}.")
    if not inputs_directory.is_dir():
        raise ValueError(f"Input directory not found at {inputs_directory}.")
    if not ground_truth_directory.is_dir():
        raise ValueError(f"Ground-truth directory not found at {ground_truth_directory}.")

    settings = _load_settings(prompt_directory / "settings.yaml")
    seed_prompt = resolve_seed_prompt(seed_prompt_path, output_directory, resume=resume, console=console)
    cases = _load_eval_cases(inputs_directory, ground_truth_directory)
    config = _build_config(seed_prompt, cases, settings)
    console.print(
        Panel(
            f"Prompt Model configuration created with {len(cases)} evaluation cases and one deterministic routing metric.",
            title="Transcript Sectioning Optimization",
            border_style="cyan",
        )
    )
    console.print(Syntax(config.model_dump_json(indent=2), "json"))
    if not run:
        return

    if cross_validate and holdout_prefix is not None:
        raise ValueError("Choose either --cross-validate or --holdout-prefix, not both.")
    if holdout_prefix is not None:
        asyncio.run(_run_group_holdout(seed_prompt, cases, settings, output_directory, holdout_prefix, console))
        return
    if cross_validate:
        asyncio.run(_run_cross_validation(seed_prompt, cases, settings, output_directory, console))
        return

    try:
        result = asyncio.run(
            optimize_prompt(
                config=config,
                metrics=[TranscriptSectioningMetric()],
                scorer=WeightedMeanScorer(settings.metric_weights),
                on_checkpoint=lambda prompt: checkpoint_callback(output_directory, prompt),
            )
        )
    except BaseException as exc:
        report_interruption(exc, output_directory, console, title="Transcript Sectioning Optimization")
        raise
    prompt_path = save_winner(
        output_directory,
        result.best_prompt,
        {"mode": "full_corpus", "result": result.model_dump(mode="json")},
    )
    console.print(
        Panel(
            f"Best score: {result.best_score:.4f}\nWinner saved to: {prompt_path}",
            title="Transcript Sectioning Optimization Complete",
            border_style="green",
        )
    )
