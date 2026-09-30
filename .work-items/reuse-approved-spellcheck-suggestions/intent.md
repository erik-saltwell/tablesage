# Reuse approved glossary spellcheck suggestions — intent

## Outcome

Help a campaign catch recurring spelling mistakes that the current session's LLM misses. Each campaign retains approved From → To corrections, including whether they are case sensitive. The current session's review combines applicable remembered corrections with fresh LLM suggestions. Reviewers remain in control of what is applied and what the campaign remembers.

The agreed quality dimensions are [correction coverage, suggestion correctness, and review efficiency](rubric.md). Numerical anchors are not yet defined.

## Campaign memory and current suggestions

- Learn a mapping from a session's **Review Transcript → Find/Replace (`F`)** only when Review Transcript is completed. Find/Replace must have changed at least one occurrence, and both its From and To values must contain non-whitespace text. Preserve the case-sensitivity choice. Saving an unfinished transcript draft does not teach memory; discarding it does not teach memory.
- Also learn retained corrections when a session's **Spellcheck Against Glossary** review is committed. An edited remembered row replaces the original mapping on commit. A removed row is forgotten on commit, regardless of whether it was removed automatically or by the reviewer.
- Seed existing campaigns **once** from approved spellcheck decisions saved in their existing sessions. Earlier Find/Replace operations cannot be reliably recovered because they were not recorded separately. Later removal must not be undone by scanning that old history again.
- Show a remembered mapping alongside the current LLM suggestions only when its From text matches the current transcript under its saved case-sensitivity setting. A mapping without a match stays in memory for future sessions. Deduplicate identical mappings in the combined list.
- Forgetting removes a mapping from campaign memory. It does not block a fresh LLM suggestion for the same mapping in a later session; that suggestion can be reviewed and approved again.

Forgetting and learning are changes to current campaign memory, not a rule to reapply every historical review whenever it is opened. Completing an older review without changing its decisions leaves memory unchanged. A new edit, restore, or removal in that review takes effect when committed.

## Review behavior

Use a visible, restorable **Keep/Remove** state like Assign Utterances to New Players in both the glossary spellcheck proposal list and the Review Transcript utterance list. Removed rows stay in their session's review history when the review is reopened, so the reviewer can restore them later. Only kept rows contribute to the committed correction or reviewed transcript. Changes made while a review is unfinished are provisional; cancelling the review leaves campaign memory unchanged. A saved draft keeps the unfinished row states for later review without committing them.

Sort correction rows by From text, ignoring capitalization, so competing mappings sit together. For several mappings with the same From text, leave one active by a consistent ordering and initially mark the others removed. The user has no preference for the particular tie-break rule. Restoring one alternative automatically marks the currently active mapping removed, keeping one active mapping per source. Each row retains its own case-sensitivity setting, even when grouped with differently capitalized rows.

Committing spellcheck review remembers kept mappings and forgets mappings left removed, including alternatives that were automatically marked removed. The final row state determines the outcome. Removed rows remain visible in that session's review if it is reopened, despite being absent from campaign memory. Simply reopening and completing an unchanged old review must not replay these memory changes.

## Observable acceptance conditions

- A committed correction from either source can appear in a later session whose transcript contains a match, even when that session's LLM misses it. It remains available after intervening sessions without a match.
- LLM and remembered suggestions that represent the same mapping appear once. Competing replacements for one From text appear together, with one active; restoring an alternative switches the active mapping.
- The review shows removed correction and utterance rows and allows them to be restored, including after reopening a completed review.
- Committing a removed correction forgets it from future remembered suggestions; cancelling or saving a draft leaves campaign memory unchanged. An unchanged older review does not revive a forgotten mapping.
- Existing saved spellcheck approvals seed campaign memory once; subsequent decisions remain authoritative. Existing historical Find/Replace operations are not inferred from final transcript text.
- Case-sensitive and case-insensitive mappings match future transcript text according to the setting the reviewer approved.

## Remaining implementation choices

Choose a stable tie-break ordering, mapping identity for deduplication, storage and migration strategy, and how to preserve review row state across drafts and completed reviews. These choices must support the behavior above. No particular database schema or UI layout beyond grouping and Keep/Remove was agreed.
