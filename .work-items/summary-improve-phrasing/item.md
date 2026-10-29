---
name: "Improve Phrasing"
status: complete
---

# Improve Phrasing

Improve how the Session Summary sounds when a GM uses it aloud at the table: headings and their bullets that read as one natural spoken unit, sentence case, and one consistent grammatical person. On 2026-10-28 this replaced three separate captured items, which are closed: [summary-heading-listenability](../summary-heading-listenability/), [summary-sentence-case](../summary-sentence-case/), [summary-consistent-voice](../summary-consistent-voice/). The immediate-danger item was split back out as its own item, [summary-immediate-danger](../summary-immediate-danger/).

The matching Table Recap items remain separate because Table Recap generation is paused pending redesign: [table-recap-heading-listenability](../table-recap-heading-listenability/), [table-recap-sentence-case](../table-recap-sentence-case/), [table-recap-consistent-voice](../table-recap-consistent-voice/).

Current approach (revised 2026-10-28): each Matters prompt writes its Summary text read-aloud-ready, and the Summary stays a deterministic template render; see the revision note in [idea.md](idea.md) and [progress.md](progress.md). The original workshop result is in [idea.md](idea.md): a single LLM phrasing pass rewrites the Summary from Post-Session Matters while leaving the Matters themselves unmodified, items that have not changed reuse the previous Session's wording, and the new headings are settled. Where the review notes below differ from idea.md, idea.md wins.

## Settled decisions (2026-10-28)

1. **One voice (reverted 2026-10-28 at the user's direction; the Matters text refers to the party as "the party" again, while the headings keep their wording):** use second person ("you") throughout, because the GM is speaking to the players. Bullets about the whole party become "you" ("You caught the Clurichen…", not "The Party Caught…"). Bullets about one character keep that character's name ("Dr. Uriah must give penance…").
2. **Heading readability:** headings are phrased so they can be read aloud verbatim without sounding awkward, working as spoken lead-ins to their lists.
3. **Sentence case:** both headings and bullet text use normal sentence case, not Title Case.
4. **Bullets fit their heading:** each bullet is a complete, standalone phrase starting with a capital letter that reads naturally after its heading, without repeating or clashing with it. Under "You learned", write "The smith is the cult leader", not "You learned that the smith is the cult leader". Bullets are deliberately not grammatical continuations of the heading (such as "that the smith is…"). Reasons: Matters items are reused by later extractors, future Sessions and the Table Recap; continuations would break when a heading is reworded; and complete phrases are easier for the GM to scan and for the prompts to produce reliably.

The sections below are the original review notes; where they differ, these decisions win.

## Headings and bullets that sound natural aloud

Rephrase the section headings so that, said aloud, they work as natural spoken transitions. A GM using the Summary at the table speaks the headings as segues between lists, and written-document headings sound stilted when spoken.

Current headings ([session_summary.j2](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2)): "Previously", "You learned", "You acquired the following resources", "Your goals remain", "Standing in your way", "Openings", "Remaining Questions", "Commitments", "Meanwhile", "As we return", "The immediate danger". The worst offenders are "You acquired the following resources" (wordy and formal) and the bare nouns "Openings", "Commitments" and "Remaining Questions", which don't flow as speech. The final headings are settled in [idea.md](idea.md#headings-settled).

Also rephrase each section's child bullets so they read naturally right after their heading. A GM reads the heading and then each bullet as one spoken unit, so a bullet should continue the heading rather than repeat it or clash with it. For example, under "You learned" a bullet starting "You learned that…" sounds odd aloud; it should start directly with what was learned (see decision 4). The same applies to whatever headings are adopted: bullet phrasing and heading phrasing have to be designed together. Superseded: rather than teaching each Matters prompt its heading, a single phrasing pass sees headings and bullets together (see [idea.md](idea.md#mechanism-settled)).

Constraints: headings stay short and scannable for the GM; keep consistent with the one-voice decision below. Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md).

## Sentence case for item text

Write headings and item text in sentence case instead of Title Case (decision 3). Headline-style bullets such as "Sir Phidipaldi Stripped Sir Brandon's Armor From His Corpse as the Party Looted the Tomb" read like newspaper headlines and are harder to scan and paraphrase.

Most affected in the Summary: the Previously and You learned bullets, and the heading "Remaining Questions". The Table Recap's "Last time" and "You learned" sentences have the same problem. Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md).

Resolved by the workshop: the phrasing pass applies sentence case; the Matters prompts and their stored text are unchanged (see [idea.md](idea.md#mechanism-settled)).

## One consistent voice

Use one grammatical person throughout. Headings address the players ("Your goals remain", "You learned", "Standing in your way") while bullets use third person ("The Party Caught…", "Trout's party must…", "Dr. Uriah must…"). The mixed voice makes paraphrasing aloud awkward.

Decided: second person; individual character names stay where an item concerns one character (decision 1).

Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md). Item text comes from the Matters prompts, and headings from [session_summary.j2](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2).

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28, treating them as material a GM uses at the table. The user prefers short, paraphrasable bullet lists over read-aloud box text.

Completed 2026-10-28 at the user's direction. Outcome:
- Summary headings are spoken lead-ins.
- The ten Matters prompts write sentence-case bullets fitted to their headings.
- The party stays "the party"; second person was reverted.
- The Summary is a deterministic template render.

Verification:
- ruff and ty pass.
- An offline layout check confirmed the Summary layout is unchanged apart from headings.
- A live Regenerate All Outputs run on Brandonsford produced sentence-case, heading-fitted Summaries, in second person; it ran before the revert.

Limits:
- The second-person revert hasn't been regenerated or checked with a live run. The deployed Summaries still contain "you" until the next Regenerate All Outputs, which will rebuild every Matters category and the 002–004 Scene Logs.
- No quality rubric was defined or scored. See [progress.md](progress.md).
