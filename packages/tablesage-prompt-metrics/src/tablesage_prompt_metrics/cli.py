from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from prompt_model.config import LiteLLMConfig

from .bundle import EvaluationBundle, export_ledger_bundle
from .profiles import write_profiles
from .questions import generate_questions


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export and prepare TableSage prompt-evaluation bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export-ledger", help="Export an exact production Ledger evaluation bundle.")
    export_parser.add_argument("campaign", help="Campaign name.")
    export_parser.add_argument("session", help="Three-digit session sequence, such as 001.")
    export_parser.add_argument("output", type=Path, help="Destination directory for the local bundle.")
    export_parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="TableSage repository/data root.")
    export_parser.add_argument("--force", action="store_true", help="Replace an existing bundle directory.")

    question_parser = subparsers.add_parser("generate-questions", help="Replace a bundle's editable completeness questions.")
    question_parser.add_argument("bundle", type=Path, help="Evaluation bundle directory.")
    question_parser.add_argument("--model", default="anthropic/claude-sonnet-5", help="Question-generation model.")
    question_parser.add_argument("--target-words", type=int, default=2500, help="Approximate words per transcript chunk.")
    question_parser.add_argument("--overlap-lines", type=int, default=8, help="Overlapping transcript lines between chunks.")
    return parser


async def _generate(args: argparse.Namespace) -> None:
    bundle = EvaluationBundle(args.bundle)
    questions = await generate_questions(
        bundle,
        LiteLLMConfig(model=args.model, temperature=0.0),
        target_words=args.target_words,
        overlap_lines=args.overlap_lines,
    )
    print(f"Wrote {len(questions)} editable questions to {bundle.root / 'questions.json'}")


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if args.command == "export-ledger":
        bundle = export_ledger_bundle(
            args.repo_root,
            args.campaign,
            args.session,
            args.output,
            overwrite=args.force,
        )
        smoke_path, full_path = write_profiles(bundle)
        print(f"Exported Ledger evaluation bundle to {bundle.root}")
        print(f"Prompt Forge profiles: {smoke_path.name}, {full_path.name}")
        return 0
    if args.command == "generate-questions":
        asyncio.run(_generate(args))
        return 0
    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
