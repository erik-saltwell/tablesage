# Voice print terminology

Replaced the old terminology and the one-word prose spelling with “voice print” / “voice prints” across implementation, UI labels and messages, public docs, internal work-item records, benchmark scripts, and the local ignored archive. Python identifiers use `voice_print`, `voice_prints`, and `VoicePrintResult`. Renamed the benchmark module to `benchmarks/speaker_id/voice_print.py` and updated imports. Existing tests were renamed to follow the API; no tests were added.

The player model now stores `voice_print_embedding`. Migration `c1d2e3f4a5b6` renames the existing database column without changing its contents. The historical player-table migration and the new upgrade/downgrade must retain the original column name to support old databases. These are the only remaining references to the old terminology in maintained source.

The public concept definition explicitly covers a single utterance or a collection of samples. Mean/outlier computation behavior is unchanged. Existing unrelated working-tree edits were preserved.

Verification:

- Ruff checks passed for packages, TUI, benchmarks, the sample-data script, and both speaker-ID experiment scripts.
- `ty check` passed.
- Existing benchmark tests: 16 passed.
- Disposable database checks passed for fresh creation, populated upgrade, downgrade, and re-upgrade; embedding contents, sample count, and dimension were preserved.
- Renamed module/document link destinations resolve; `git diff --check` passed.
- Full existing project test suite: 738 passed in 179.61 seconds.

No numerical rubric or quality scores were defined. The requested rename is complete.
