# Reuse approved glossary spellcheck suggestions

## Intended effect

Glossary spellcheck currently misses too many corrections. Give each campaign a memory of approved text replacements so recurring mistakes can be suggested even when the current session's LLM misses them. Preserve reviewer control and keep the combined list manageable.

The following proposal was agreed at the end of the workshop. It describes product behavior; implementation has not started.

## Campaign correction memory

A campaign remembers approved From → To mappings from two sources:

- Applied **Find/Replace (`F`)** operations in the session's Review Transcript screen.
- Approved corrections from previous sessions' glossary spellcheck review.

For a new session, combine the LLM's suggestions with remembered mappings whose From text matches the current transcript. Deduplicate identical mappings.

A remembered mapping with no current matches stays in campaign memory but does not appear in this session's suggestions. It can appear again in a later session where it matches. Absence of a match does not mean rejection or forgetting.

## Review interaction and competing mappings

Use the existing **Keep/Remove** interaction from Assign Utterances to New Players in both of these places:

- The glossary spellcheck review's list of proposed corrections.
- The Review Transcript screen's list of utterances.

Removed rows stay visible, visibly marked as removed, and restorable rather than disappearing immediately. Their final kept/removed state controls whether they are included when the review is committed.

Sort correction proposals by From text so competing mappings appear together as ordinary rows. If several distinct mappings have the same From text, leave only the first active and automatically mark the rest removed while still showing them. Use a consistent ordering to determine the first mapping; the user has no preference for a particular tie-break rule. The reviewer can change row states before committing.

Multiple mappings for the same source are treated as an exceptional or broken case. The agreed approach is sorting and a simple default, rather than a separate conflict-resolution interface.

## Learning, forgetting, and commitment

Campaign memory changes when the corresponding action is committed:

- An applied Find/Replace operation teaches its mapping when the replacement is applied.
- Committing glossary spellcheck review remembers retained mappings and forgets every mapping left in the removed state.
- Keep/Remove toggles during an unfinished review are provisional. Cancelling that review leaves campaign memory unchanged.

The final state is authoritative regardless of how a row became removed. An automatically removed competing mapping is forgotten if the reviewer leaves it removed on commit, just like a manually removed mapping. Restoring a mapping and retaining it on commit makes it eligible for future suggestions.

This explicitly replaces the workshop alternative in which automatic removal would preserve a mapping in campaign memory. The user preferred one simple rule and considers competing mappings an edge case.

## Expected benefits and limits

The approved quality dimensions are recorded in [rubric.md](rubric.md).

- **Correction coverage:** both approval sources capture recurring mistakes; retaining unmatched memory preserves its usefulness across sessions.
- **Suggestion correctness:** remembered approval provides evidence, but a text match does not prove that a replacement fits every context. Consistent ordering of competing mappings does not guarantee that the first is correct.
- **Review efficiency:** matching before display, deduplication, sorting, and visible reversible removal reduce clutter and repetitive cleanup. Committing memory changes with the review allows provisional decisions to be reversed.

These are judgments of the unbuilt design's potential, not measured results. The workshop ended with agreement that the proposal was sufficiently coherent and simple to document; no additional features were selected.

## Questions at the end of the workshop

The later [agreed intent](intent.md) resolves these questions and is authoritative for the feature's current behavior.

The precise mapping identity and matching rules, consistent tie-break ordering, storage design, and whether existing historical approvals are initially imported remain unspecified. The behavior when a reviewer restores several competing mappings also remains unspecified.

Forgetting removes a mapping from the remembered suggestions added to future reviews. Whether to suppress an independently generated future LLM suggestion for that same mapping was not decided.

Numerical rubric anchors and calibration remain unresolved. The user explicitly chose to proceed with workshop using the agreed dimensions qualitatively.
