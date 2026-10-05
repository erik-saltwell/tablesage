# Player Voice Sample Review Implementation

Implement the saved [intent](intent.md). The user explicitly requested implementation without a rubric; no numerical quality assessment is available. Preserve Player Detail's immediate confirmed deletion and R/C maintenance actions while adding P playback and V review.

- [x] Add application preparation that cleans up valid samples, ranks surviving clips against the resulting voice print, reports unscorable clips, and applies multiple removals with one recomputation. Use deployed remove_outliers settings and report partial file changes on failure.
- [x] Add a shared playback table using the existing ReviewPlayback controller, Player Detail playback, and Review Outliers with fixed ranking, 20-row batches, crossed-out removal, Continue, Cancel, and quit handling.
- [x] Run lint/type/build checks and behavior-level verification, including the real application layer in an isolated fixture workspace. Use Textual MCP to check navigation, loading, removal/restoration, discard prompts, and capture Player Detail and Review Outliers. Do not create or expand unit tests.
- [x] Update the guide, Players reference, screen index, Common UI Patterns, and screenshots. Record verification and mark the item complete when all required work is done.
- [x] Make Player Detail enter silently in Manual mode, preserving clip playback on clicks and arrow navigation; verify entry, refresh, reopening, and return from Review Outliers, and update the guide/reference and Player Detail screenshot.

Inspected application.py, voice_clips/clips.py, embeddings/similarity.py, player_detail.py, audio_playback.py, screen/base.py, main_app.py, app.tcss, AppSettings, packaged settings.yaml, and documentation fixture scripts. The existing cleanup algorithm aborts if embedding a single sample fails; preparation will retain and report unscorable files while applying the same duplicate/outlier cleanup algorithm to usable samples. Existing voice print computation already returns retained embeddings, but cleanup currently discards them; preparation will cache embeddings for ranking. Screenshots will use fictional fixtures without changing a user's samples.
