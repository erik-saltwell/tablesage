# Update from Reviewed Transcripts

This one-off maintenance utility accepts existing human-reviewed transcripts as authoritative checkpoints and optionally rebuilds a Campaign's downstream outputs using the current application. It is separate from normal processing and has no new UI action. Adoption does not certify historical audio, transcription, speaker-identification, or spellchecking steps as current.

Close TableSage and finish all processing before running it. Back up the complete workspace first. The utility checks reviewed transcripts and protected narrative inputs against that backup and retains saved review decisions and drafts. It refuses missing, changed, empty, or invalid review inputs rather than silently reconstructing them. All Sessions in the selected Campaign must have distinct dates and valid processing metadata.

## Preview

From the checkout:

```sh
uv run python scripts/migrate_reviewed_sessions.py \
  --workspace ~/data/tablesage_summary_test \
  --backup ~/data/tablesage_summary_backup.2gftGS/workspace \
  --campaign Brandonsford
```

Preview lists Session dates, transcript checksums, utterance counts, adjusted counts, configured generation model, and rebuild order. It neither adopts reviews nor calls models. It opens an existing initialized workspace through the normal application/settings loader; this is not a general read-only forensic tool for an unmigrated database.

## Adopt and Regenerate

Select a new receipt directory under `summary_experiment/migrations/`:

```sh
uv run python scripts/migrate_reviewed_sessions.py \
  --workspace ~/data/tablesage_summary_test \
  --backup ~/data/tablesage_summary_backup.2gftGS/workspace \
  --campaign Brandonsford \
  --output ~/data/tablesage_summary_test/summary_experiment/migrations/reviewed-transcript-update-20261005 \
  --apply --generate
```

`--apply` alone adopts the reviews without generating outputs. `--generate` explicitly enables model calls, using the workspace's deployed model and generation timeout and normal local credential configuration. Never include credentials in a receipt or chat.

Generation first reopens downstream output completion records, then rebuilds Role Transcript, Transcript Sections, Ledger with Scene Breakdown, Player Introductions, Recap Summary, and Summary in dependency and Session-date order. It writes canonical generated outputs in the testing workspace. The backup preserves their originals. Reviewed transcripts and historical decision/draft sections are checked after adoption and after each Session completes.

`receipt.json` records the source revision, implementation hashes, controls, transcript checksums, current phase, completed Session task lists, and failure type. The shared LLM client supplies native structured-output support and published limits for Opus 5.5 when the bundled LiteLLM catalog is older than that model, avoiding forced-tool requests and truncated responses. This restores documented model metadata; explicit per-call output limits still override defaults. See [LiteLLM Anthropic support](https://docs.litellm.ai/docs/providers/anthropic#structured-outputs) and [Opus 5.5 specifications](https://platform.claude.com/docs/en/models/opus-5-5/overview).

A partial failure leaves successful outputs and the checkpoint in place. It does not roll back or hide completed model calls. Retain the receipt and logs.

Opus 5.5 requests stream internally and are assembled into a complete response before normal validation and persistence. The deployed generation timeout also bounds the full streaming call, including receipt of all chunks; incomplete or interrupted streams fail without returning partial output. This follows [Anthropic's guidance for long requests](https://platform.claude.com/docs/en/api/errors#long-requests) to avoid idle connections while waiting for large responses. It does not change model, prompt, or generation controls.

## Resume

Repeat the same applied command with `--resume` and the same receipt directory. This also allows an adoption-only receipt to continue with `--generate`:

```sh
uv run python scripts/migrate_reviewed_sessions.py \
  --workspace ~/data/tablesage_summary_test \
  --backup ~/data/tablesage_summary_backup.2gftGS/workspace \
  --campaign Brandonsford \
  --output ~/data/tablesage_summary_test/summary_experiment/migrations/reviewed-transcript-update-20261005 \
  --apply --generate --resume
```

Resume requires unchanged Session inputs, generation controls, and implementation hashes. It keeps completed outputs and rebuilds only what remains stale or missing. Task receipts are saved after a Session completes; a failed Session may have some successfully generated phases not yet listed, and its ordinary artifact completion records determine the remaining work.

## Verify and Continue

A completed run requires current reviewed transcripts and all generated artifacts, with protected inputs and saved decisions unchanged. Open TableSage and inspect the outputs before using them for the experiment. Earlier processing rows can remain out of date because they describe historical machine work. The processing coordinator resumes after an accepted review rather than automatically rerunning those rows. Existing output-regeneration actions can use the checkpoint. Explicitly restarting earlier processing or replacing the review revokes acceptance.

The application records `reviewed_transcript_checkpoint` in `processing_state.json` with Session ID, checksum, adoption time, revision, and backup reference. Missing or changed reviewed-transcript bytes make it stale. Hashes are change detection, not a tamper-proof signature. Older application versions do not recognize this acceptance; retain the backup and use the current version.
