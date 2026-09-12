"""Prompt Forge workflow for optimizing the Recap Summary prompt."""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from prompt_model import OptimizationResult, optimize_prompt
from prompt_model.config import EvalCase, LiteLLMConfig, OptimizerConfig
from prompt_model.scorers import WorstCaseAggregator
from pydantic import BaseModel, ConfigDict, Field
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from tablesage_application.llm import PromptName
from tablesage_application.llm._prompts import read_prompt_template

from .ledger_metrics import JsonQuestionFactory
from .recap_evaluation import RecapRunObserver, evaluate_recap, write_json
from .recap_summary_metrics import RecapLengthSettings, build_recap_summary_metrics, extract_scene_breakdown
from .recap_summary_scorer import RecapSummarySearchScorer
from .winner_output import checkpoint_callback, resolve_seed_prompt, save_winner


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
    alignment_threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    length: RecapLengthSettings
    judge_attempts: int = Field(default=3, ge=1)


class RecapSourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["scene_breakdown_v1"]
    template_sha256: str
    scene_breakdown_sha256: dict[str, str]


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


async def validate_corpus(prompt_directory: Path, cases: list[EvalCase]) -> None:
    """Fail before paid calls on invalid sources or missing/invalid curated questions."""
    for case in cases:
        extract_scene_breakdown(case.input)
    expected_stems = {Path(case.source_path).stem for case in cases if case.source_path is not None}
    for name in ("coverage_questions", "recognition_questions", "exclusion_questions"):
        directory = prompt_directory / name
        actual_stems = {path.stem for path in directory.glob("*.json")}
        if actual_stems != expected_stems:
            raise ValueError(
                f"{name} must match evaluation inputs: missing {sorted(expected_stems - actual_stems)}, "
                f"orphaned {sorted(actual_stems - expected_stems)}."
            )
        factory = JsonQuestionFactory(directory)
        for case in cases:
            await factory.questions(case.input, case.source_path)
    validate_source_manifests(prompt_directory / "inputs", cases)


def validate_source_manifests(inputs_directory: Path, cases: list[EvalCase]) -> None:
    """Detect mixed, edited, or stale snapshots without depending on local campaign files."""
    template_digest = hashlib.sha256(read_prompt_template(PromptName.GENERATE_RECAP_SUMMARY).encode("utf-8")).hexdigest()
    expected: dict[str, str] = {}
    for path in sorted(inputs_directory.glob("*_sources.json")):
        manifest = RecapSourceManifest.model_validate_json(path.read_text(encoding="utf-8"))
        if manifest.template_sha256 != template_digest:
            raise ValueError(f"Recap template changed since {path.name} was generated; regenerate evaluation inputs.")
        duplicates = expected.keys() & manifest.scene_breakdown_sha256.keys()
        if duplicates:
            raise ValueError(f"Duplicate recap source provenance: {sorted(duplicates)}.")
        expected.update(manifest.scene_breakdown_sha256)
    names = {case.source_path for case in cases}
    if names != expected.keys():
        raise ValueError("Source manifests must cover exactly the recap inputs; regenerate evaluation inputs.")
    for case in cases:
        if case.source_path is None:
            raise ValueError("Recap evaluation inputs require a filename source_path.")
        digest = hashlib.sha256(extract_scene_breakdown(case.input).encode("utf-8")).hexdigest()
        if digest != expected[case.source_path]:
            raise ValueError(f"Scene Breakdown snapshot for {case.source_path} differs from its manifest; regenerate inputs.")


def corpus_fingerprint(prompt_directory: Path, settings: RecapSummarySettings) -> str:
    """Bind checkpoints to the source, questions, seed, models, and scoring implementation."""
    digest = hashlib.sha256(settings.model_dump_json().encode())
    paths = [prompt_directory / "seed_prompt.txt", Path(__file__)]
    for name in ("inputs", "coverage_questions", "recognition_questions", "exclusion_questions"):
        paths.extend(sorted((prompt_directory / name).glob("*")))
    paths.extend(
        Path(__file__).with_name(name)
        for name in ("recap_summary_metrics.py", "recap_summary_scorer.py", "recap_evaluation.py", "recap_alignment.py")
    )
    for path in paths:
        if path.is_file():
            digest.update(str(path.relative_to(prompt_directory) if path.is_relative_to(prompt_directory) else path.name).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def optimize_recap_summary(
    prompt_directory: Path,
    console: Console,
    *,
    run: bool = False,
    resume: bool = False,
    evaluate: bool = False,
    case_name: str | None = None,
    prompt_path: Path | None = None,
    iterations: int | None = None,
) -> None:
    if run and evaluate:
        raise ValueError("Choose --run or --evaluate, not both.")
    if (case_name is not None or prompt_path is not None) and not evaluate:
        raise ValueError("--case and --prompt require --evaluate; optimization always uses the full corpus.")
    if resume and not run:
        raise ValueError("--resume requires --run.")
    if iterations is not None and (not run or iterations < 1):
        raise ValueError("--iterations requires --run and a positive count.")
    seed_prompt_path = prompt_directory / "seed_prompt.txt"
    inputs_directory = prompt_directory / "inputs"
    output_directory = prompt_directory / "outputs"
    if not seed_prompt_path.is_file():
        raise ValueError(f"Seed prompt not found at {seed_prompt_path}.")
    if not inputs_directory.is_dir():
        raise ValueError(f"Evaluation inputs directory not found at {inputs_directory}.")

    settings = _load_settings(prompt_directory / "settings.yaml")
    if iterations is not None:
        settings.optimizer.iterations = iterations
    cases = _load_eval_cases(inputs_directory)
    asyncio.run(validate_corpus(prompt_directory, cases))
    fingerprint = corpus_fingerprint(prompt_directory, settings)
    manifest_path = output_directory / "checkpoint_manifest.json"
    if resume:
        if not manifest_path.is_file() or not (output_directory / "checkpoint.md").is_file():
            raise ValueError("No compatible checkpoint found; start a fresh run without --resume.")
        if json.loads(manifest_path.read_text())["fingerprint"] != fingerprint:
            raise ValueError("Checkpoint inputs, settings, or scoring changed; start a fresh run without --resume.")
    config = OptimizerConfig(
        seed_prompt=resolve_seed_prompt(seed_prompt_path, output_directory, resume=resume, console=console),
        eval_cases=cases,
        target_llm=settings.target_llm,
        actor_llm=settings.actor_llm,
        judge_llm=settings.judge_llm,
        **settings.optimizer.model_dump(),
    )
    metrics = build_recap_summary_metrics(
        judge_llm=config.judge_llm,
        coverage_question_directory=prompt_directory / "coverage_questions",
        recognition_question_directory=prompt_directory / "recognition_questions",
        exclusion_question_directory=prompt_directory / "exclusion_questions",
        length=settings.length,
        judge_attempts=settings.judge_attempts,
    )
    scorer = RecapSummarySearchScorer(alignment_threshold=settings.alignment_threshold)
    if not config.seed_prompt.strip():
        raise ValueError("Seed prompt is empty.")
    console.print(
        Panel(
            f"Prompt Model configuration created with {len(config.eval_cases)} evaluation cases and {len(metrics)} metrics.",
            title="Recap Summary Optimization",
            border_style="cyan",
        )
    )
    console.print(Syntax(config.model_dump_json(indent=2, exclude={"eval_cases", "seed_prompt"}), "json"))
    console.print(f"Cases: {', '.join(case.source_path or '(unnamed)' for case in cases)}")
    console.print(f"Length limits: {settings.length.model_dump()}; alignment gate: {settings.alignment_threshold}")
    console.print("Search objective: improve the weakest case; strict acceptance is reported separately.")
    if not run and not evaluate:
        return
    # The direct library entry point does not run Prompt Forge's CLI dotenv setup.
    load_dotenv(override=False)
    selected_cases = cases
    if case_name is not None:
        selected_cases = [case for case in cases if case.source_path == case_name]
        if not selected_cases:
            raise ValueError(f"Unknown case {case_name!r}; use an exact input filename.")
    run_directory = output_directory / "runs" / uuid.uuid4().hex
    write_json(
        run_directory / "run.json",
        {"fingerprint": fingerprint, "mode": "evaluate" if evaluate else "optimize", "settings": settings.model_dump(mode="json")},
    )
    console.print(f"Run evidence: {run_directory}")
    if evaluate:
        prompt = prompt_path.read_text(encoding="utf-8") if prompt_path else config.seed_prompt
        if not prompt.strip():
            raise ValueError("Evaluation prompt is empty.")
        report = asyncio.run(
            evaluate_recap(prompt, selected_cases, config.target_llm, metrics, settings.alignment_threshold, run_directory / "evaluation")
        )
        console.print(f"Strict acceptance: {report['accepted']}; mean search score: {report['mean_search_score']:.4f}")
        return
    # Persist the seed immediately, so a failure in warmup still has an honest restart point.
    write_json(manifest_path, {"fingerprint": fingerprint})
    checkpoint_callback(output_directory, config.seed_prompt)

    async def run_pipeline() -> tuple[dict[str, Any], OptimizationResult, dict[str, Any]]:
        baseline = await evaluate_recap(
            config.seed_prompt, cases, config.target_llm, metrics, settings.alignment_threshold, run_directory / "baseline"
        )
        result = await optimize_prompt(
            config=config,
            metrics=metrics,
            scorer=scorer,
            on_checkpoint=lambda prompt: checkpoint_callback(output_directory, prompt),
            observer=RecapRunObserver(run_directory / "search_events.jsonl"),
            survivor_case_aggregation=WorstCaseAggregator(),
            final_case_aggregation=WorstCaseAggregator(),
        )
        checkpoint_callback(output_directory, result.best_prompt)
        write_json(run_directory / "search_result.json", result.model_dump(mode="json"))
        validation = await evaluate_recap(
            result.best_prompt, cases, config.target_llm, metrics, settings.alignment_threshold, run_directory / "validation"
        )
        return baseline, result, validation

    try:
        baseline, result, validation = asyncio.run(run_pipeline())
    except BaseException as exc:
        write_json(run_directory / "failure.json", {"error_type": type(exc).__name__, "error": str(exc)})
        console.print(f"Run failed: {type(exc).__name__}: {exc}")
        console.print(f"Restart prompt preserved at {output_directory / 'checkpoint.md'}; evidence: {run_directory}")
        console.print("Use --run --resume with the same settings to restart from the saved prompt.")
        raise
    prompt_path = save_winner(
        output_directory if validation["accepted"] else run_directory,
        result.best_prompt,
        {
            "mode": "full_corpus",
            "fingerprint": fingerprint,
            "settings": settings.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
            "baseline": baseline,
            "validation": validation,
            "accepted": validation["accepted"],
            "run_directory": str(run_directory),
        },
    )
    console.print(
        Panel(
            f"Search score: {result.best_score:.4f}\nSelected candidate saved to: {prompt_path}\n"
            f"Fresh full-corpus strict acceptance: {validation['accepted']}",
            title="Recap Summary Optimization Complete",
            border_style="cyan",
        )
    )
