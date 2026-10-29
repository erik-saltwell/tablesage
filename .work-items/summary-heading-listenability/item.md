---
name: "Session Summary: rephrase headings for listenability"
status: complete
---

# Session Summary: rephrase headings for listenability

Rephrase the section headings so that, said aloud, they work as natural spoken transitions. A GM using the Summary at the table speaks the headings as segues between lists, and written-document headings sound stilted when spoken.

Current headings ([session_summary.j2](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2)): "Previously", "You learned", "You acquired the following resources", "Your goals remain", "Standing in your way", "Openings", "Remaining Questions", "Commitments", "Meanwhile", "As we return", "The immediate danger". The worst offenders are "You acquired the following resources" (wordy and formal) and the bare nouns "Openings", "Commitments" and "Remaining Questions", which don't flow as speech. Example directions, not decisions: "You picked up…", "What's in your way", "Still unanswered".

Also rephrase each section's child bullets so they read naturally right after their heading. A GM reads the heading and then each bullet as one spoken unit, so a bullet should continue the heading rather than repeat it or clash with it. For example, under "You learned" a bullet starting "You learned that…" sounds odd aloud; it should start directly with what was learned. The same applies to whatever headings are adopted: bullet phrasing and heading phrasing have to be designed together. Bullet text comes from the Matters prompts, so this probably means each prompt needs to know the heading its output appears under.

Constraints: headings stay short and scannable for the GM; keep consistent with the one-voice decision in [summary-consistent-voice](../summary-consistent-voice/). Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md).

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28, treating them as material a GM uses at the table. The user prefers short, paraphrasable bullet lists over read-aloud box text.

Closed without implementation on 2026-10-28 at the user's direction; merged into [Improve Phrasing](../summary-improve-phrasing/), where work continues.
