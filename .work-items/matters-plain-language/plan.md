# Plan: Clearer Matters Wording

## Goal

Change the Matters prompts so every bullet the Session Summary shows is easier to understand on first reading and easier to say aloud, without losing any fact, condition, amount, attribution or uncertainty. The settled wording rules, examples, scope and approved quality rubric are in [intent.md](intent.md); this plan does not restate them in full. The change is prompt text and one contract amendment only: no Python, template, schema, layout, qualification or lifecycle changes.

The four rules, for reference: put the actor and action early; use familiar verbs and everyday wording; break crowded sentences into two short sentences within the same bullet; keep qualifications beside the claim, source first. Clear entries and carried-forward wording stay word for word.

## What was inspected (2026-10-28)

All prompts are under `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_matter_<category>/`.

- **Prompt loading.** `prompt_loader.py` reads each `system.md` as raw text; there is no include mechanism. Shared guidance must be duplicated into each prompt.
- **Freshness.** `application.py` (`_narrative_graph`, `bundle`) registers each Matters prompt's `system.md`, `template.j2` and `schema.json` as freshness dependencies. Editing a prompt makes that category's Matters stale in every Session, and the dependency graph cascades to Post-Session Matters, the Session Summary and later Sessions' Matters. Regeneration makes LLM calls for all four Brandonsford Sessions.
- **Schemas.** No `schema.json` has a description on the Summary fields, so no schema edits are needed.
- **Summary rendering.** `session_pipeline/session_summary.py` `_sentence` only collapses whitespace and adds a final period when missing. A two-sentence bullet renders correctly, with no code change.
- **Summary fields.** The Summary reads Developments `title`, Revelations `text`, New Assets `name`, `title` for Goals, Goal Impediments, Opportunities, Mysteries, Obligations and Brewing Troubles, and Present Matters `current_position` and `present_danger`. Other fields (`benefit`, `details`, `opening`, `anticipated_development` and so on) are not shown and are out of scope.
- **Every prompt** has a `### Read-aloud wording for <field>` section (Present Matters: `# Read-aloud wording`) from [Improve Phrasing](../summary-improve-phrasing/item.md), with sentence-case and heading-fit bullets. This is where the shared rules go.
- **Contract.** [Matters Port specification](../port-tablesage-matters-artifacts/specification.md) line 19 says the Opportunity title "is one short, simple sentence"; line 25 describes Revelations as keeping "its concise headline structure". Both need an amendment.

### Current output used as the baseline

The deployed Brandonsford Sessions 001–004 were regenerated on 2026-10-28 between 16:47 and 17:05 and contain no leftover second person, so they are a clean baseline. Representative problems in `deployment/campaigns/Brandonsford/<session>/summary.md`:

- Opportunity (004): "Getting the dragon to drink enough of the party's faun wine could knock it out, according to Vivian, so its mouth can be reached." Source after the claim, passive ending, one crowded sentence.
- Opportunity (001–003): "Lady Hilda, a seasoned warrior, will join the party against the dragon if they pay her, adding a capable fighter." Aside plus a trailing clause.
- Opportunity (002): "Retrieving Sir Brandon's magic sword from the Barrow Mound could make killing the dragon possible, according to Father William." Source last.
- Present Danger (003): "A seven-foot brown skeleton … stands in the tomb's doorway blocking the party's only exit; it is likely the very big figure that the goblins and the slime say killed the goblins and is undead and very mad, though its intent is unknown." Stacked clauses, buried attribution.
- Current Position (001, 003): long semicolon chains, one clause per group.
- Development (002): "Dunk agreed to help Ingrid drug Warwick so she could watch him sleep, while hinting he might reveal her secret." Crowded.

Many entries are already clear and must stay unchanged, for example most Goals, Obligations and Mysteries, and the New Assets names.

## Decisions made in this plan

These are agent recommendations; the user has not reviewed them yet.

1. **One shared rules block, copied into all ten prompts,** because prompts cannot include shared files. Identical wording keeps the categories consistent; category-specific examples go in the category sections.
2. **Hypothetical examples** in the shared block (the miller and the ferryman from the intent, plus a hypothetical attribution), so the model does not copy campaign facts between categories. The Vivian rewrite stays in the intent as evidence, not as prompt text.
3. **Mysteries stay one question.** A Mystery title is defined as one direct question, and changing that would change classification, which is out of scope. Rule 3 applies there by keeping the question short, not by splitting it.
4. **New Assets `benefit` is out of scope.** It is not shown in the Summary, so its "one concise sentence" rule stays. This corrects the conflict list in the intent.
5. **Developments and Revelations keep their headline style,** but may use a second short sentence when one headline would otherwise stack clauses. Explanatory follow-up sentences stay banned.
6. **Baseline snapshots stay out of Git.** Campaign outputs live under the git-ignored `deployment/`; the snapshot goes to `deployment/baselines/matters-plain-language/`, outside `campaigns/` so the app never reads it.

## Phase 0: Snapshot the baseline

- [x] Copy `summary.md` and `post_session_matters.json` for Brandonsford 001–004 to `deployment/baselines/matters-plain-language/<session>/`.

Verification: the four snapshot `summary.md` files match the deployed files byte for byte (`cmp`).

## Phase 1: Add the shared plain-wording rules to all ten prompts

- [x] Append the block below to the end of each read-aloud section, after the existing sentence-case and heading-fit bullets, in: Developments, Revelations, New Assets (applies to `name` only), Goals, Goal Impediments, Opportunities, Mysteries, Obligations, Brewing Troubles, Present Matters.

Proposed block (final wording may be tightened during implementation, keeping each rule):

```markdown
Write each bullet so the Game Master understands it on first reading and can say it aloud without stumbling:

- Put the actor and the action early, so it is immediately clear who did, believes, offers or owes something. Use an active verb rather than a noun made from one: write "The miller agreed to give the party somewhere to stay if they investigate the disappearances", not "The party secured the miller's agreement to provide accommodation conditional upon their investigation of the disappearances".
- Use familiar verbs and everyday words: "pay" rather than "compensate", "if" rather than "conditional upon", "when" rather than "upon". Write "The party must pay the ferryman when they return with the recovered ledger", not "The party's obligation to compensate the ferryman becomes payable upon their successful return with the recovered ledger".
- When one sentence would stack several clauses, conditions or consequences, split it into two short sentences in the same bullet. Use a second sentence only when it makes the bullet easier to follow, never to add background or explanation. Avoid asides set off by commas, semicolons or brackets.
- Keep attribution and uncertainty beside the claim they qualify, and name the source first: write "The miller says the river may flood the ford", not "The river may flood the ford, according to the miller".
- Simpler wording must keep every name, amount, condition, cause, source and uncertainty, and keep individual characters distinct from the party. If a bullet is already clear, do not rewrite it.
```

Verification: each of the ten `system.md` files contains the block exactly once, inside its read-aloud section (`grep -c`). Read each edited section once in context to check it does not contradict the surrounding guidance.

## Phase 2: Resolve category conflicts

### Opportunities (`generate_matter_opportunities/system.md`)

- [x] Line 13 (`title` field description): replace "one short, simple, read-aloud sentence" with a short, simple read-aloud title of one sentence, or two short sentences when one would be crowded.
- [x] Line 54 (`Setting title`): same change to "Write one short, simple sentence". Keep the 15–25-word guide as a guide for the whole title, with more words allowed when needed.
- [x] Line 56 good example: change to source-first, for example "Father William says retrieving Sir Brandon's sword from the Barrow Mound could help slay the dragon."
- [x] Line 66 read-aloud example: remove the trailing clause, for example "Lady Hilda will fight the dragon alongside the party if they pay her."
- [x] Line 122 (`Final wording pass`): replace "in one sentence" with the one-or-two-sentence wording, and replace "Rewrite carried entries to the current structure" with the carried-forward rule in Phase 3 (detailed fields may still be brought to the current structure; a carried title stays word for word unless it breaks the rules or its facts changed).
- [x] Line 130 JSON output example `title`: make it source-first, matching the line 56 example.

### Brewing Troubles (`generate_matter_brewing_troubles/system.md`)

- [x] Line 150: change "In one short sentence" to allow a second short sentence when a condition or consequence would otherwise crowd the title. Keep "preserve an accurate existing title" and extend it in Phase 3.

### Developments (`generate_matter_developments/system.md`)

- [x] Line 65: change "omit the terminal period" so it applies only to the end of the title, since a second sentence needs an internal period.
- [x] Line 67: change "Avoid … explanatory follow-up sentences" so a second short sentence carrying an essential condition or consequence is allowed, while explanations stay banned.

### Revelations (`generate_matter_revelations/system.md`)

- [x] Line 80: same two adjustments as Developments ("Omit the terminal period"; "Use no … explanatory follow-up sentence").

### Present Matters (`generate_matter_present_matters/system.md`)

- [x] Line 3: when the party is split, give each group its own short sentence rather than its own semicolon clause.
- [x] Line 7 good example: "Mira and Tobin are in the flooded bell vault beneath the lighthouse. Corvin is on the quay with Captain Sella."
- [x] Line 35 good example: "…stands in the tomb's only doorway. Its intent is unknown."

### Goal Impediments (`generate_matter_goal_impediments/system.md`)

- [x] Line 69 ("Keep useful uncertainty and attribution"): add "naming the source before the claim".

### Mysteries and New Assets

- [x] Mysteries: in the read-aloud section, state that a title stays one question and is kept clear by short wording, not by splitting (decision 3).
- [x] New Assets: state that the shared rules apply to `name`, which may stay a short noun phrase. No change to `benefit` (decision 4).

Verification: re-run the earlier scan for one-sentence limits and trailing attributions (`one short`, `one sentence`, `, according to`, `, <Name> says`) across all `generate_matter_*/system.md`; only intentional uses remain (Mysteries' one question, New Assets' `benefit`). Read each edited section in context.

## Phase 3: Keep carried-forward wording stable

Carried rule text, adapted to each prompt's terms:

```markdown
When a previous entry carries forward and its facts, terms and lifecycle are unchanged, copy its existing title word for word. Reword it only when it breaks the plain-wording rules above or when its facts, terms or lifecycle have changed.
```

- [x] Goals, line 103: extend "Preserve existing titles unless they are inaccurate, unclear, or insufficiently specific" with "or break the plain-wording rules", and state that preserved titles are copied word for word.
- [x] Goal Impediments: add the rule near line 53, where carried IDs are reconciled. There is currently no wording-preservation rule.
- [x] Mysteries, line 88: replace "preserve continuity through the underlying question and recognizable wording" with the rule; the question remains the continuity key.
- [x] Obligations: add the rule to the reconciliation step around line 25 or the title guidance at line 83. There is currently no wording-preservation rule.
- [x] Brewing Troubles, line 150: extend "preserve an accurate existing title" with the rule.
- [x] Opportunities, line 122: covered in Phase 2.

Not applied to Developments, Revelations and New Assets, which describe only the current Session, or to Present Matters, which restates the current stopping point each Session.

Verification: each of the six prompts contains one carried-wording instruction, and no prompt still tells the model to rewrite carried titles.

## Phase 4: Amend the contract

- [x] [Matters Port specification](../port-tablesage-matters-artifacts/specification.md): add a dated amendment note referencing this item. The primary Summary fields follow the plain-wording rules. The Opportunity title (line 19) is one sentence or two short sentences. Developments and Revelations headlines may add a second short sentence for an essential condition or consequence (line 25). Carried titles are copied word for word unless they break the rules or their facts change.
- [x] Check the [Deterministic Session Summary specification](../deterministic-table-recap/specification.md) needs no change; it already copies Matters wording as written.

Verification: read the amended section; confirm it does not contradict the Improve Phrasing amendment (sentence case, heading fit, "the party").

## Phase 5: Regenerate and evaluate

- [ ] Run Regenerate All Outputs for Brandonsford in the TUI. This makes LLM calls for every Matters category in all four Sessions. Confirm with the user before running it.
- [ ] Diff each regenerated `summary.md` against the Phase 0 snapshot.
- [ ] Record the evaluation in `evaluations.md`, judged in words against each of the five rubric dimensions in [intent.md](intent.md#quality-rubric-approved-2026-10-28). Name the prompt version (Git commit or working-tree date) and the rubric definition. Cover at least:
  - the baseline problem entries listed above (Opportunities, Present Danger, Current Position, crowded Developments);
  - already clear entries and carried titles, for "Rewording only where needed" (for example, Goals and Obligations that carry across 002–004 should be word for word unless their facts changed);
  - each attribution and hedge, for "Meaning kept" and "Hedges easy to notice";
  - each Open Matters category at least once.
- [ ] Note any dimension that cannot be judged from Brandonsford alone as unassessed.

Verification: the evaluation exists, covers all five dimensions, and records anything left unassessed. Regeneration completes without validation failures; any retries or failures go into `progress.md`.

LLM output varies between runs, so one regeneration shows tendencies rather than proof. If results are mixed, adjust prompt wording and regenerate again, recording each round.

## Material unknowns

- Whether the model actually copies carried titles word for word when instructed. Matters prompts receive previous entries as JSON, but there is no code-side enforcement. If drift persists, code-side preservation would be a separate decision outside this plan's prompt-only scope.
- Whether allowing a second sentence makes some bullets longer without making them clearer. The "Easy to say aloud" dimension is where this shows.
- Regenerating every Brandonsford output also re-runs other Matters logic; unrelated differences (qualification, lifecycle) may appear in the diff and must be separated from wording changes.
