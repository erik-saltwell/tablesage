---
name: "Glossary-first transcript review"
status: complete
---

# Glossary-first transcript review

Run the existing Role Transcript glossary extraction and review UI as the first
phase of transcript review. Approved glossary additions commit immediately;
afterwards, the existing spelling-correction and manual transcript review flow
continues. Cancelling during glossary review saves no proposals and exits the
entire review; cancelling later leaves the glossary commit in place while
discarding transcript edits.

## Completion

- Implemented the glossary proposal phase in `ManualReviewScreen`, including
  automatic continuation when extraction returns no new terms.
- Reused `GlossaryReviewScreen` and made its dismiss result distinguish
  approval from cancellation so it can act as an embedded phase without
  changing standalone extraction behavior.
- No numerical rubric exists; this was a user-directed implementation request.
- Verified with `uv run pytest apps/tablesage-tui/tests/test_glossary_review.py
  apps/tablesage-tui/tests/test_speaker_review.py
  apps/tablesage-tui/tests/test_speaker_review_suggestions.py
  apps/tablesage-tui/tests/test_session_detail.py` (82 passed), targeted Ruff
  lint, and `git diff --check`.
