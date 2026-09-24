# Plan: Isolate New Speakers sample yield

## Intent

Isolate New Speakers (`session_pipeline/isolate_new_speakers.py`) proposes candidate utterances for each new player. Review New Speaker Assignments can only remove candidates. Whatever survives becomes the seeds a later step uses to search the session by voice.

This step therefore has two jobs:
- **Enough candidates:** give review enough good candidates to choose from for every player.
- **Pure candidates:** keep them voice-pure, especially the ones sent to the later voice search as seeds.

Searching the session by voice here is out of scope, because a later step already does it.

## What happened (Brandonsford 001, 2026-09-24)

The session had 5 attendees, all new players: Jason (GM), Erik, John, Rich, and Marshall. The transcript had 1,787 utterances.

**Final counts:** each player ended with 1 utterance of 4–11 s. The GM ended with 243 utterances (about 1,790 s).

**Where the picks went:**
- **The LLM picks were right but short.** They were correct attributions but proof lines: replies to direct address such as "Human.", "Dagonite assassin.", and "Yes.".
- **The length filter removed most of them.** 14 of the 17 player picks were under `min_speech_seconds` (3.0 s) and were dropped. Even the full set of picks was under 15 s for every player.

**What the table looked like:**
- **Players rarely spoke for 3 s or more.** `speaker_0` had 22 such utterances out of 360; `speaker_2` had 27 of 438; `speaker_3` had 0 of 29; `speaker_4` had 1 of 52. The GM (`speaker_1`) had 244 of 908.
- **Play was short.** It started at about minute 76 of 117.

**How the fallback failed:**
- **Merged voices.** Diarization was already given `num_speakers=5` and returned 5 labels, but it merged voices. `speaker_0` held Erik, John, and probably Marshall; `speaker_2` held Rich and Marshall.
- **Shared labels were skipped.** The fallback ignores any label proposed for more than one player, so four players got nothing from it.
- **The GM's label was swept whole.** The GM's unique label pulled in all 244 of its ≥3 s utterances.

**Sources:**
- Log: `~/data/tablesage/.tablesage/logs/tablesage.log`, `op: isolate_new_speakers`.
- LLM output: `.tablesage/logs/prompts/2026-09-24_11-09-38-616102_output.md`.

## Approved changes

1. **Length floor of 1.0 s** for every utterance, covering both LLM picks and fallback additions (was 3.0 s).
2. **Coverage-aware prompt:**
   - Show each row's speech duration.
   - State the per-player speech target and ask for longer lines.
   - Add spotlight exchanges and GM-only speech (narration, rulings, NPC voices) as valid evidence.
   - Replace "precision matters far more than coverage" with "if uncertain, leave it out".
   - Keep "never list the same utterance for two players".
3. **Cap and order the fallback pool.** For the fallback additions only, never the player's LLM picks:
   1. Collect every eligible utterance of 1.0 s or more.
   2. Drop the shortest additions until the pool is at or under `fallback_max_speech_seconds` (60 s), or every addition is at least 2.0 s.
   3. Run the existing outlier removal.
   4. If the pool is still over the cap, drop the additions least similar to the player's seed centroid until it's at or under the cap.
   - **Seed centroid:** built from the player's kept LLM picks when those total at least 5 s of speech. Otherwise use the pool's own centroid.
   - **LLM picks:** never cut and never counted against the cap.
4. **Player names instead of UUIDs in the prompt:**
   - The prompt and response use player names.
   - The response schema constrains `player_name` to an enum of the supplied names.
   - Names are mapped back to UUIDs deterministically. Unknown names are dropped and counted in diagnostics, as unknown UUIDs are today.
   - UUIDs stay in every artifact.
   - This applies only to `isolate_new_speakers`. Other prompts that use UUIDs are a possible follow-up.
5. **Unique names when adding players and attendees.** See the Phase 4 note: exact uniqueness is already enforced.

**Refused or deferred:**
- **Refused:** a voice seed search from LLM picks across all labels, because a later step already does this.
- **Refused:** passing the speaker count to diarization, which already happens (`transcribe_audio.py:116-131`).
- **Deferred:** splitting shared labels by voice clustering. Revisit if a rerun still leaves shared-label players thin.

## Follow-up changes (approved 2026-09-24, after the first rerun)

- **P1, exchanges in and out of character:** the spotlight rule is generalized. Once someone addresses a player or character by name, that player's replies in the back-and-forth that follows are theirs, until someone else is addressed or joins in. This applies in and out of character, including rules questions, character creation, and table talk.
- **P2, crosstalk filter:** implemented and then removed at the user's direction. ElevenLabs never gives overlapping times to two labels, so it could not detect anything.
- **Label-only evidence rule:** a speaker label is never evidence on its own. It can only add confidence to an utterance the conversation already ties to a player.
- **P3, label-first ownership:** the LLM is given the label list with counts and seconds, and answers per label: a player name, `(mixed)`, or `(other)`. Only one owner is possible per label.
  - The label and answer values are enums, with the same strict mode as the names.
  - `proposed_speaker_ids` was removed from the per-player answer. The artifact field is now derived from the mapping.
  - **Cross-check:** a label is not used for a player's fallback if another player's claimed picks fall on it.
- **P4, prefer the natural voice:** deferred.

## Code inspected

- `packages/tablesage-application/src/tablesage_application/session_pipeline/isolate_new_speakers.py`:
  - response models (`EvidenceEntry`, `PlayerUtterancesResponse` keyed by `player_id`);
  - `IsolationSettings`, `_ask_llm`, `_build_assignments` (filtering and fallback at lines 217–277);
  - `_without_voice_outliers`.
- `.../llm/_prompts/isolate_new_speakers/system.md` and `template.j2`.
- `.../application.py:1840-1860`: `Application.isolate_new_speakers` builds `IsolationSettings` from `speaker_bootstrap` and `remove_outliers`.
  - **Pitfall:** `speaker_bootstrap.min_speech_seconds` is also used by bootstrap candidate selection (`application.py:1460`), so the 1.0 s floor must not be set there.
  - The review step reads `speaker_bootstrap.min_total_speech_seconds` (`application.py:1880`).
- `packages/tablesage-model/src/tablesage_model/settings/app_settings.py`: `SpeakerBootstrapSettings`.
- `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`: `speaker_bootstrap` section.
- `packages/tablesage-tools/src/tablesage_tools/embeddings/similarity.py`: `compute_centroid` returns only `centroid` and `unused_paths`. It exposes neither per-clip embeddings nor similarities.
- `.../entities/players.py`:
  - `create_player` gets a unique-name `IntegrityError` from `Player.name` (`unique=True`).
  - `rename_player` gets the same error via `_fs.rename_named_entity`.
- `.../entities/sessions.py`:
  - `add_attendance` and `set_attendance_player` rely on `uq_session_attendance_session_id_player_id`.
- `.../llm/llm_helper.py`: `response_model` is a pydantic class passed through as `response_format`.

## Structured-output enforcement (checked 2026-09-24)

`call_llm` sends `response_format={"type": "json_schema", "json_schema": {name, schema}}` without `"strict": true`. A direct litellm probe (1.100.1) used a two-name `enum` and a system prompt that pushed the model to rewrite the names and add a third player:

| Model | `strict` | Result |
|---|---|---|
| `openai/gpt-5.6-terra` (the deployed `llm_model`) | absent (current) | **Not enforced.** It returned `Erik "The Fool" Saltwell` and an invented `Rich`, which failed pydantic validation 2 out of 2 times |
| `openai/gpt-5.6-terra` | `true`, with `additionalProperties: false` | Enforced, 2 out of 2 |
| `anthropic/claude-sonnet-4-5` (the packaged default `llm_model`) | absent | Enforced, 2 out of 2 |
| `anthropic/claude-sonnet-4-5` | `true` | Enforced |

What this means:

- **The deployed model needs strict mode.** On OpenAI the schema is only a hint unless `strict` is set.
  - Without it, a bad name fails validation in `_ask_llm`, which already raises on invalid output and retries up to `evidence_max_attempts`.
  - So the failure mode is a failed step, not silent misattribution.
- **Strict mode brings its own risk.** It can make the model coerce a name it would otherwise have invented into a valid one. In the probe, it filed the prompted "Rich" under `John Schork`.
  - In real use every attendee is supplied, so there is little pressure to invent.
  - The prompt must still say not to list anyone outside the supplied names.
  - Review stays the backstop.

## Phases

### Phase 1: Settings

- [x] Add an `isolate_new_speakers` section to `AppSettings`, following the `remove_outliers` precedent:
  - `min_speech_seconds: 1.0`;
  - `fallback_short_clip_seconds: 2.0`;
  - `fallback_max_speech_seconds: 60.0`;
  - `min_seed_speech_seconds: 5.0`.
- [x] Validate the new values:
  - all positive;
  - `fallback_short_clip_seconds` at least `min_speech_seconds`.
- [x] Add the section, with comments, to the packaged `settings.yaml`.
- [x] Extend `IsolationSettings` with the new fields plus `target_total_speech_seconds`, which is reused from `speaker_bootstrap` for the prompt. Populate it in `Application.isolate_new_speakers` from the new section.
- [x] Leave `speaker_bootstrap.min_speech_seconds` unchanged, since bootstrap still uses it.

**Expected outcome:** the knobs come from `settings.yaml`, and bootstrap behavior is unchanged.

**Verification:**
- Type-check the model and application packages.
- Load the packaged settings and an existing user `settings.yaml` without the new section; defaults should apply.

### Phase 2: Names instead of UUIDs, and the coverage-aware prompt

- [x] Replace `player_id` with `player_name` in `EvidenceEntry` and `PlayerUtterancesResponse` for the LLM response only. Build the response model per call with `pydantic.create_model`, using `Literal[*names]`, so the JSON schema carries an enum.
- [x] Make the enum actually enforced on OpenAI. See "Structured-output enforcement" below.
  - Add an opt-in `strict_schema: bool = False` to `tablesage_tools.llm.call_llm`, passed through `call_llm_with_prompt`. When it's set, add `"strict": true` to the `json_schema` response format, and set `additionalProperties: false` with every property required on every object in the schema.
  - Use it only for `isolate_new_speakers`, whose response models have no optional fields or `oneOf` unions.
  - Keep strict off globally. Other prompts' schemas (for example discriminated unions, which produce `oneOf`) may not meet OpenAI's strict-mode subset.
- [x] Map names back to player IDs in `_build_assignments` with an exact lookup.
  - Count unknown names in diagnostics.
  - Stored `EvidenceEntry` records in `new_speaker_assignments.json` keep `player_id`. Split the stored model from the response model so the artifact schema doesn't change.
- [x] Update `template.j2`:
  - list players by name and roles, without UUIDs;
  - show rows as `[i] speaker=speaker_N (X.Xs): text`, using `speech_duration`;
  - pass the speech target.
- [x] Update `system.md` with the approved wording changes (change 2).

**Expected outcome:** every player gets more and longer evidence-backed picks, and the output is readable without looking up IDs.

**Verification:**
- Rerun Isolate New Speakers on Brandonsford 001.
- Compare the prompt trace output and the `isolate_new_speakers` diagnostics against the 2026-09-24 run: `llm_utterance_count`, `kept_from_llm`, and `final_speech_seconds` per player.
- Check the prompt trace to confirm the response schema contains the name enum.

### Phase 3: Floor and capped fallback

- [x] Use `settings.min_speech_seconds` (1.0) for both LLM picks and fallback eligibility. Leave `_REQUIRE_EVIDENCE` as it is.
- [x] Rework the fallback in `_build_assignments` into the pipeline from change 3: length stage, then outlier removal, then similarity stage. LLM picks are held out of every stage and added back at the end.
- [x] Extend `compute_centroid` in `tablesage-tools` to also return the kept paths' embeddings, or their similarity to a supplied reference centroid. It must stay generic: plain values, no settings objects.
- [x] Build the seed centroid from the player's kept picks when they total at least `min_seed_speech_seconds`, and rank additions by cosine similarity to it.
- [x] Add diagnostics:
  - `fallback_dropped_short`;
  - `voice_outliers_removed`;
  - `fallback_dropped_dissimilar`;
  - `seed_source`, either `picks` or `pool`;
  - `fallback_added_seconds`.

**Expected outcome:**
- No player receives more than about 60 s of fallback additions. The GM drops from 243 clips to roughly 15–30.
- Players with unique labels get additions, now including clips of 1–3 s.

**Verification:**
- Rerun on Brandonsford 001 and read the diagnostics.
- Open Review New Speaker Assignments in the TUI and confirm clip counts per player are reviewable.
- Spot-listen to several fallback clips per player to check voice purity.

### Phase 4: Unique names for players and attendees

What's already true:
- **Exact player names are unique.** The DB enforces this (`Player.name unique=True`), and both `create_player` and `rename_player` report a clear error.
- **Attendee names are unique too.** A player can attend a session only once, so exact uniqueness among attendee names follows.

So the exact-match lookup in Phase 2 is already safe.

**Decided 2026-09-24:** player names are always unique ignoring case (and surrounding spaces).

- [x] `tablesage_model.player_names.player_name_key` (strip + casefold). `create_player` and `rename_player` refuse a name whose key matches another player's; changing the case of your own name is allowed.
- [x] `add_attendance` and `set_attendance_player` refuse an attendee whose key matches another attendee in the session. This guards against players created before the rule.
- [x] Player-archive import merges folders that differ only by case (or surrounding spaces) into one player: the existing player's name if there is one, otherwise the tidiest spelling. Clashing clip filenames are renamed while staging. `test_player_archive.py::test_empty_archive_and_exact_names` was updated to the new rule and renamed `..._case_variant_names`.
- Existing collisions: none in the user's workspace (5 players checked).

**Verification:**
- In the TUI, try to create, rename, and add an attendee with a colliding name, and confirm each is refused with a clear message.
- Check that existing workspaces still load.

## Material unknowns

- **Strict mode on other providers:** strict mode was probed only against `openai/gpt-5.6-terra` and `anthropic/claude-sonnet-4-5`. Recheck if `llm_model` changes to another provider.
- **Short-clip reliability:** how the later voice-search step handles clips of 1–2 s hasn't been checked.
- **Thresholds are starting points:** the 1.0 s floor, 60 s cap, and 5 s seed minimum should be tuned after the rerun.
