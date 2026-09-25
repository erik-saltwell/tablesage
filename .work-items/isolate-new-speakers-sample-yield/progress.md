# Progress: Isolate New Speakers sample yield

## Status (2026-09-24)

All phases are implemented and verified, with follow-up decisions recorded below. It is ready for broader user testing.

## What changed

- **Settings:** `tablesage_model.settings.IsolateNewSpeakersSettings` is exposed as `AppSettings.isolate_new_speakers` and added to the packaged `settings.yaml`.
  - Fields: `min_speech_seconds` 1.0, `fallback_short_clip_seconds` 2.0, `fallback_max_speech_seconds` 60, `min_seed_speech_seconds` 5.
  - `speaker_bootstrap.min_speech_seconds` is unchanged, since bootstrap still uses it. The prompt's target reuses `speaker_bootstrap.target_total_speech_seconds`.
  - `SETTINGS_VERSION` was not bumped, following the `name_corrections` precedent. Existing workspaces get the defaults.
- **`tablesage-tools`:**
  - `call_llm(strict_schema=...)` sends `"strict": true` and closes every object schema (`additionalProperties: false`, all properties required).
  - `CentroidResult.embeddings` holds the embeddings of the clips that were used.
  - `cosine_similarity` is exported.
- **`llm_helper.call_llm_with_prompt(strict_schema=...)`** passes the flag through. It is only forwarded when set, so existing test fakes still work.
- **`isolate_new_speakers.py`:**
  - The LLM sees and answers with player names. The response model is built per call with a `Literal` enum of the names, using strict mode.
  - Names map back to ids. Unknown names are logged under `_unknown_player_names`. Duplicate new-player names raise.
  - The stored `EvidenceEntry` still uses `player_id`, so the artifact schema is unchanged.
  - The fallback is now `_capped_fallback`: length stage, then outlier removal on the additions only, then the similarity stage against the picks (at least 5 s) or the pool. LLM picks are never trimmed.
  - New diagnostics: `kept_from_llm_seconds`, `fallback_dropped_short`, `voice_outliers_removed`, `seed_source`, `fallback_dropped_dissimilar`, `fallback_added_seconds`.
- **Prompt:**
  - Rows show `(X.Xs)`, and the coverage targets are given.
  - Evidence now includes spotlight exchanges and GM-only speech.
  - "Precision matters far more than coverage" became "if uncertain, leave it out".
  - The model is told to name only the supplied players.

## Verification

- **Static checks:** `ruff check`, `ruff format --check`, and `ty check` pass on the changed files.
- **Existing tests:** `pytest packages apps --ignore=apps/optimize-prompts` gives 688 passed. `apps/optimize-prompts` fails to collect because `optimize_prompts` isn't installed; that is unrelated. No tests were added.
- **Real rerun of Isolate New Speakers on a copy of Brandonsford 001** (`/tmp/iso_rerun/001`, with the user's deployed settings, `openai/gpt-5.6-terra`):
  - `call_llm` logged `strict_schema: true` and `structured_response_valid: true`. The LLM call took 48 s.

  | Player | Before (utterances / s) | After (utterances / s) |
  |---|---|---|
  | erik saltwell | 1 / 10.9 | 4 / 45.5 |
  | John Schork | 1 / 5.3 | 5 / 12.8 (shared label, so no fallback) |
  | rich gredzinski | 1 / 4.1 | 10 / 28.5 |
  | jason beaumont (GM) | 243 / 1789.5 | 4 / 40.2 |
  | marshall riser | 1 / 4.2 | 7 / 16.0 |

  - Every pick was read against its transcript text. All are plausible for the named player, including spotlight exchanges such as Rich's necklace scene (1601–1667).
  - No player needed the fallback except John, whose label is shared.
- **Fallback exercised directly** (`_capped_fallback` on the GM's `speaker_1` pool: 557 utterances, 2,310 s):
  - Seeded from picks: 220 dropped as short, 1 outlier, 333 dropped as dissimilar. 3 clips kept, 37.7 s total, shortest 9.1 s. Took 133 s.
  - Seeded from the pool: 3 clips kept, 48.5 s total. Took 122 s.
- **Not checked:**
  - The TUI review screen with the new artifact.
  - Listening to the clips.
  - How the later voice-search step handles clips of 1–2 s.

## Follow-up P1–P3 (2026-09-24)

- **Implemented:**
  - P1, the exchange rule in the prompt.
  - P2, `_crosstalk_indices` with the `dropped_crosstalk` diagnostic.
  - P3, the `speaker_labels` answer with name, `(mixed)`, and `(other)` enums. The picks cross-check is logged as `mixed_by_picks`, and the label mapping as `speaker_label_owners`.
- **Checks:**
  - ruff and ty are clean.
  - `pytest packages apps --ignore=apps/optimize-prompts` gives 688 passed.
  - `_crosstalk_indices` matches `bootstrap_speakers.has_cross_speaker_overlap` on utterances 1150–1449 and takes 0.08 s over the whole transcript.
- **P2 finds nothing on ElevenLabs output.** It reports 0 crosstalk utterances across the transcript. ElevenLabs never gives overlapping word or utterance times to two labels; talk-over is split into back-to-back segments, and 88 of 1,426 label changes have a gap of 0 s or less. It was later removed; see "Follow-up decisions".
- **Third rerun on the copy:** strict mode valid; the LLM call took 48 s.
  - Labels: `speaker_0` (mixed), `speaker_1` jason, `speaker_2` rich, `speaker_3` (mixed), `speaker_4` marshall. `mixed_by_picks` was empty.

  | Player | Run 2 | Run 3 |
  |---|---|---|
  | erik saltwell | 4 / 45.5 s | 7 / 40.5 s |
  | John Schork | 5 / 12.8 s | 7 / 15.9 s |
  | rich gredzinski | 10 / 28.5 s | 9 / 24.4 s |
  | jason beaumont | 4 / 40.2 s | 3 / 44.2 s |
  | marshall riser | 7 / 16.0 s | 17 / 31.0 s |

  - Every player met `min_total_speech_seconds` from picks alone, so the fallback did not run.
- **Label chaining (watch in user testing):**
  - Marshall's 17 picks are all character-creation questions on `speaker_4` (877–1096).
  - The only conversational anchor is 867–868: the GM asks "Marsh, you have all your armor?" and `speaker_4` replies.
  - The LLM then chained the following `speaker_4` lines to Marshall by label, even though the exchange rule should have ended at 869, when the GM addresses John.
  - It is probably correct here, since `speaker_4` is a small label that is quiet during play. But it is attribution by diarization label, not by conversation.

## Follow-up decisions (2026-09-24)

- **P2 removed.** The crosstalk filter and its diagnostics are gone.
- **Label-only evidence rule added to the prompt.**
  - Run 4 on the copy gave: erik 5 clips / 37.4 s, John 4 / **10.4 s**, rich 9 / 31.9 s, jason 2 / 32.9 s, marshall 11 / 24.5 s. Marshall's picks moved from `speaker_4` character-creation questions to his in-play Dunk lines.
  - John's total varies run to run (12.8, 15.9, 10.4 s), and his label is mixed, so the fallback adds nothing.
  - The per-label answers also vary: run 3 said `speaker_2` is Rich; run 4 said `speaker_2` is mixed and `speaker_3` is Rich, even though all of Rich's picks are on `speaker_2`. This only matters when the fallback runs. A possible fix is to give a player a label only when their own picks fall on it; not decided.
- **P4 deferred.**
- **Phase 4 done (case-insensitive names):** see plan.md.
  - A throwaway workspace confirmed each case. Blocked: creating or renaming to a name that differs only by case, and attending or reassigning to a player whose name clashes with another attendee's. Allowed: changing the case of your own name, and reassigning a row to a clashing player that replaces the same attendee.
  - An archive import with real clips put two differently cased folders into the existing player: 4 unique clips, 1 duplicate skipped, the filename clash kept. Two new-player variants became one player.
- **Checks:** ruff and ty are clean across all packages. `pytest packages apps --ignore=apps/optimize-prompts` gives 688 passed.

## Review screen tidy-up (2026-09-24, at the user's request)

- **Changes to `screens/new_speaker_assignments.py`:**
  - Removed the "Mode: Auto/Manual" indicator; Space still toggles the mode, as shown in the footer.
  - Removed the "Evidence: …" / "Added by voice match" line under the utterances.
  - Both tables now have border-title headers: "Players" and "Utterances · <player>".
  - The columns contain only their tables, so the panes share top and bottom edges.
- **Checks:**
  - A headless `run_test()` at 160×45 and 120×30 with the rerun's real review data showed matching `region.y` and `region.bottom` for both tables, and the header following the selected player. A screenshot was also checked.
  - TUI tests: 285 passed.

## Players pane width and end-user test (2026-09-24)

- **Players pane:** now `width: 50%`, `min-width: 57`, `max-width: 64`, so "Too little speech" fits. Checked with `run_test()` at 160×45 (64 wide) and 120×30 (57 wide). At 120×30 the Utterances pane shrinks to 46 columns and its text is cut off sooner.
- **End-user test through the Textual MCP server,** on a copy of the workspace (`/tmp/tablesage_uat`, the user's real data untouched), with real LLM calls. Flow:
  1. Campaign, then session 001, then Process Session.
  2. Step 2, Review Name Corrections: two suggestions that would replace whole phrases were deleted ("Eric will just" and "Hi im, Eric" → "erik saltwell").
  3. Apply & Continue ran Isolate New Speakers (49 s) into the review screen.
  4. On the review screen: entered the utterances, removed and restored a clip (the totals updated), switched player (the header followed), and resized to 120×30.
  5. Confirmed. Steps 2, Isolate, and 3 were checked, and processing stopped at Enhance, which has no runner.
- **Results:** erik 6 clips / 61.5 s, John 6 / **13.6 s** ("Too little speech"), rich 7 / 22.8 s, jason 3 / 44.2 s, marshall 14 / 32.3 s. Label owners: `speaker_0` and `speaker_3` mixed, `speaker_1` jason, `speaker_2` rich, `speaker_4` marshall. No errors were logged.
- **UI notes (not changed):**
  - The Utterances table keeps a horizontal scrollbar after switching to a player whose lines fit, apparently because the column width from the previous player is kept.
  - The focused pane's border looks almost the same as the unfocused one in screenshots.
  - The Name Corrections LLM suggested phrase-level replacements, which would corrupt text if accepted.
- **TUI tests after the CSS change:** 285 passed.

## Removed the "Too little speech" warning (2026-09-24, at the user's request)

- **Why:** the samples a player has are used whatever the total, so the warning had no action behind it.
- **Change:** the Players table has only Player, Samples and Speech. `ReviewData.min_total_speech_seconds` and the matching parameter of `review_data` were removed, since the warning was their only use. The Players pane is back to `width: 45%; max-width: 52`, as its extra width only existed to fit the warning.
- **Checks:** a headless `run_test()` with real review data showed the three columns and aligned panes at 160×45 and 120×30. Tests: 688 passed.

## Observations for tuning

- **The similarity stage keeps only the most similar clips.** It drops clips until the total fits under the cap, so what remains is a few long clips (3 for the GM). A smaller review set is intended, but if more variety is wanted, it could stop at the cap by adding clips instead of removing them.
- **John is still short.** He has 12.8 s, below the 15 s minimum, and his label is shared with Erik and Marshall. This is the case the deferred shared-label split would address.
- **Fallback embedding cost** is about 2 minutes per player when a large label is used.

## Find More on the review screen (2026-09-25)

Designed with the user in a workshop on 2026-09-25 and implemented at their request.

- **Why:** the Isolate fallback only draws from a player's own diarization label, so John (on a mixed label) stayed around 10–16 s. The "Too little speech" warning was removed on 2026-09-24 because nothing could be done about it. Find More gives it an action, so it is back.
- **Behavior:**
  - `F` on Review New Speaker Assignments acts on the highlighted player. The player's voice is the centroid of their currently kept utterances; with none kept it declines with a message.
  - Every unused utterance with at least `isolate_new_speakers.find_more_min_speech_seconds` (2.0) of speech is ranked by its lead: similarity to the player minus similarity to the nearest rival. Rivals are known attendees' stored centroids, the other new players' kept-utterance centroids, and one centroid of this player's rejected Find More additions.
  - Excluded: anything already in any new player's list, kept or removed. The screen tracks removal by utterance index, so an utterance must never be in two lists.
  - It always adds when anything is left: enough to reach `speaker_bootstrap.target_total_speech_seconds` (30), or another target's worth when already there. The user rejected a "no more confident matches" state because every addition is reviewed.
  - Additions are marked `+`. A toast asks the reviewer to listen to them before confirming.
  - Only removed Find More additions count as rejections, as approved. Removed LLM picks and removed Isolate-fallback additions don't.
  - "Too little speech" now uses the 30 s target, not the 15 s minimum. The Players pane is back to `width: 50%; min-width: 57; max-width: 64`.
- **Code:**
  - `session_pipeline/find_voice_matches.py` (new): `VoiceMatchEmbeddings`, a per-Session embedding cache invalidated by transcript or audio mtime, and `find_voice_matches`, which logs a `find_voice_matches` wide event.
  - `tablesage_tools.embeddings.mean_centroid` (new).
  - `review_new_speaker_assignments.py`: `rejected_voice_matches` on the reviewed artifact; `review_data` re-shows kept and rejected additions; `save_review` accepts non-proposed indices and still compares kept sets only, so a rejection-only change isn't saved; `extract_more_clips` adds playback clips without discarding existing ones.
  - `Application.find_more_voice_matches`, and `confirm_new_speaker_assignment_review(..., rejected)`.
- **Verification:**
  - ruff, ruff format, and ty are clean. `pytest packages apps --ignore=apps/optimize-prompts` gives 642 passed. No tests were added.
  - **Backend, on a copy of the workspace** (`/tmp/tablesage_uat`):
    - John's first search embedded 446 utterances in 147 s and added 8 clips (20.7 s).
    - All 8 are utterances that the full Identify Speakers run had already labeled John. Two came from other diarization labels.
    - After rejecting two, the next search took 0.1 s and added 1 clip, reaching 30 s.
  - **TUI end to end through Textual MCP, on the same copy:**
    - At 160×45: the warning showed for Rich, Marshall, and John. John's search showed the progress dialog and took 148 s; he went from 11.5 s to 32.2 s with `+` rows and the warning cleared.
    - Removed two additions, pressed `F` again: instant, 1 clip, and the toast appeared. Erik, already at 38.6 s, gained 7 clips (32.2 s).
    - Confirm wrote the kept additions and John's `rejected_voice_matches: [806, 1539]`, and removed the clips folder.
    - Reopened at 120×30: John was back at 11 / 30.0 s, both rejected rows showed ✗, and the status column fit.
  - **Seed Player Voice Samples on the copy:** John 11 clips and Erik 14, all counted in the centroid.
  - **Not checked:** listening to the added clips, and whether the resulting profiles identify speakers better in a later Session.
- **Cost:** a Session's first search takes about 2.5 minutes, behind a progress dialog that can't be cancelled. The cache lasts for the app process, so reopening the app pays it again.

