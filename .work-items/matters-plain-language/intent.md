# Clearer Matters Wording

Improve the wording supplied by Matters to the Session Summary so the GM can scan, paraphrase, or read it aloud comfortably. Putting general clarity upstream benefits both the deterministic Summary and the Table Recap derived from it.

The goal is for each bullet to be easier to understand on the first reading and easier to say aloud, while keeping every relevant fact, condition, amount, attribution, and uncertainty.

## Wording rules (settled 2026-10-28)

The user set these four rules:

1. **Put the actor and action early.** Make it immediately clear who did, believes, offers, or owes something.
2. **Use familiar verbs and everyday wording.** Prefer "agreed to provide" over "secured an agreement for the provision of".
3. **Break up crowded sentences within the same bullet.** A bullet may use a second short sentence to separate a mechanism from its benefit, or a commitment from its condition, instead of stacking several clauses. Keep conditions and consequences clear. Do not replace a readable bullet with a long block of prose.
4. **Keep qualifications beside the claim.** Attributions such as "Vivian says" and hedges such as "may" must stay easy to notice. Put the source before the claim rather than after it.

**Leave clear entries alone.** Already clear entries need no rewriting or expansion. "Why have shipments stopped reaching Brandonsford?" stays as it is, and an asset name can remain a short noun phrase. Simpler wording must not lose meaning. Keep names, amounts, conditions, causal relationships, attribution, uncertainty, and the difference between one character and the whole party.

**Unchanged constraints.** Keep the existing sentence-case and heading-fit guidance from [Improve Phrasing](../summary-improve-phrasing/item.md): each published bullet stands on its own and reads naturally after its heading, without repeating that heading. Matters and the Summary refer to the group as "the party" and to individuals by name. Converting to second person belongs to the Table Recap presentation step.

## Examples

Hypothetical accommodation:

> The party secured the miller's agreement to provide accommodation conditional upon their investigation of the disappearances.

Becomes:

> The miller agreed to give the party somewhere to stay if they investigate the disappearances.

An actual Opportunity from the current Brandonsford output:

> Getting the dragon to drink enough of Dunk's faun wine could knock it out so you can drive Sir Brandon's sword through its mouth, Vivian says.

Becomes:

> Vivian says enough of Dunk's faun wine could knock the dragon out. If that works, the party could drive Sir Brandon's sword through its mouth.

This rewrite names the source first, separates the proposed mechanism from its possible benefit, and keeps the uncertainty.

Hypothetical dense commitment:

> The party's obligation to compensate the ferryman becomes payable upon their successful return with the recovered ledger.

Becomes:

> The party must pay the ferryman when they return with the recovered ledger.

## Apply upstream, including Open Matters

Apply the rules to the Matters prompts and fields that supply Summary text. This covers historical content (Developments, Revelations, New Assets), present content (Current Position, Present Danger), and all Open Matters categories: Goals, Goal Impediments, Opportunities, Mysteries, Obligations, and Brewing Troubles. Open Matters should receive the same clarity improvements as the events listed under "Last session...". Each category keeps its meaning: questions remain questions, commitments keep who owes what and on what terms, and possible developments remain hedged.

The Session Summary remains a deterministic render. Do not add a general rewriting LLM step to the Summary. The Table Recap consumes the improved Summary and focuses on second-person phrasing and its distinct closing-prose presentation.

This is a wording improvement only. Out of scope: which Matters qualify for publication, their lifecycle or classification, the Summary's layout, and the facts retained. The [Deterministic Session Summary specification](../deterministic-table-recap/specification.md) and the relevant Matters contracts must be consulted before implementation.

## Carried-forward wording (settled 2026-10-28)

Carried-forward entries keep their existing wording word for word unless it breaks the wording rules above. This follows the "leave clear entries alone" rule and keeps wording stable from Session to Session.

## Conflicts in the current prompts

Prompt review on 2026-10-28 found these conflicts. All paths are under `packages/tablesage-application/src/tablesage_application/llm/_prompts/`.

- **One-sentence limits.** `generate_matter_opportunities/system.md` requires the `title` to be one sentence in three places: the field description (line 13), the wording guidance (line 54), and the final wording pass (line 122). This would reject the two-sentence Vivian rewrite. `generate_matter_brewing_troubles/system.md` asks for "one short sentence" for the title. Each should allow a second short sentence where rule 3 calls for one, without making two sentences the default. (`generate_matter_new_assets/system.md` asks for "one concise sentence" for `benefit`, but the Summary shows only `name`, so that limit is out of scope; corrected during planning.)
- **Source placed after the claim.** The Opportunities prompt's full JSON output example (line 130) ends with "…could help slay the dragon, according to Father William." This contradicts rule 4 and the source-first example at line 89. It probably explains the trailing "…, Vivian says." in current output. The Goal Impediments "George says…" example (lines 61 and 97) already names the source first.
- **Carried entries rewritten every Session.** The Opportunities final wording pass says "Rewrite carried entries to the current structure" (line 122). This conflicts with the carried-forward rule above. Planning checked the other prompts that carry entries forward: none tells the model to rewrite carried titles, but only Goals and Brewing Troubles ask to preserve existing titles, and Goal Impediments and Obligations have no wording-preservation rule. See [plan.md](plan.md) Phase 3.

## Verification considerations

The deployed Brandonsford outputs were regenerated on 2026-10-28 (16:47–17:05) after the [Improve Phrasing](../summary-improve-phrasing/item.md) revert and contain no leftover second person, so they serve as the baseline. The Vivian example above was quoted from an earlier run; the current 004 Opportunity reads "Getting the dragon to drink enough of the party's faun wine could knock it out, according to Vivian, so its mouth can be reached."

Check improvements on representative outputs across categories, particularly dense Open Matters, and confirm that meaning is kept.

## Quality rubric (approved 2026-10-28)

**Subject:** the wording of Matters text that appears in the Session Summary. That covers historical, present and Open Matters bullets, and through the Summary it also shapes the Table Recap. The goal is that a GM understands each bullet on the first reading and can say it aloud comfortably, without losing any fact, condition, amount, source or uncertainty.

Each dimension is judged in words, with no scores. The user defined this rubric with the descriptive `define-rubric` skill, which takes precedence over the 0–10 scale described in `.work-items/workflow.md`. There are no scales, anchors, weights or thresholds.

1. **Understood on first reading:** A GM reading silently knows straight away who did, believes, offers or owes what, and what follows from it. This rewards putting the actor and action early, using familiar verbs and everyday wording, and saying things directly instead of hiding the action in nouns ("secured an agreement for the provision of").
2. **Easy to say aloud:** The GM can speak the bullet right after its heading without stumbling. This rewards sentence lengths you can say in one breath, natural pauses where a crowded idea is split, and wording no longer than the content needs. It also rewards avoiding constructions that only work on the page, such as nested clauses, bracketed asides or stacked conditions. Splitting a crowded bullet into two short sentences adds a little length on purpose; that tradeoff is judged here.
3. **Meaning kept:** The rewrite says exactly what the original established, without dropping or adding anything. This rewards keeping names, amounts, conditions, cause and effect, who did what, and the difference between one character and the party. It also rewards each category keeping its form: questions stay questions, promises keep who owes what, and possible developments stay possible.
4. **Hedges easy to notice:** Sources and uncertainty sit next to the claim they qualify, where a listener will catch them. This rewards "Vivian says…" and "may" over a source added at the end or a hedge buried mid-sentence.
5. **Rewording only where needed:** Changes go only where a rule was broken. This rewards leaving clear entries and short asset names alone, and keeping carried-forward wording the same from Session to Session.

**How the dimensions differ:**

- Understood on first reading and Easy to say aloud are kept separate at the user's direction. A bullet can be easy to scan but awkward to say, or smooth to say but vague about who did what.
- Meaning kept asks whether a fact or hedge survives. Hedges easy to notice asks whether a listener would actually catch it.
- Rewording only where needed is about which entries change. How long a rewritten bullet gets belongs to Easy to say aloud; the user approved this split.

No definitions are unresolved. Record evaluations separately from this definition.

## Open for later work

- The prompt changes are planned in [plan.md](plan.md); its recommended decisions await the user's review.
