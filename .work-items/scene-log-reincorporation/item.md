---
name: "Improve the summary scene log for reincorporation"
status: complete
---

# Improve the Summary Scene Log for Reincorporation

Make the Summary's Scene Breakdown much more compact and focused on information likely to be reincorporated at the table (clues, open loops, clocks, resources, commitments, relationship changes) rather than exhaustive event detail.

This continues step 3 of [Review session summary quality across various prompts](../session-summary-prompt-quality/), which found that simplifying the prompt did not bring the body near the 700-word target and that Scene Breakdown remains most of its length; see that item's [experiments](../session-summary-prompt-quality/experiments.md). Experiments reuse its [prompt harness](../../scripts/prompt_experiment.md) and frozen inputs in `/home/eriksalt/data/tablesage_summary_test/`.

See [research/](research/) for the cross-domain research behind the rubric and a transcript of the conversation that produced it.

## Closure

Closed at the user’s request on 2026-10-11. No implementation or quality verification was performed as part of this closure. The handoff below is retained as historical context; its next steps are no longer active.

## Historical Handoff (Closed)

A proposed rubric is in [rubric.md](rubric.md): seven dimensions (Anchor Coverage, Materiality, Proportional Detail, Cue Distinctiveness, Economy, Thread Legibility, Fact–Significance Separation) on a 0–10 scale, drawn from a borrowing-brilliance exploration of TV recaps, case briefs, I-PASS handoffs, retrieval cues and the Tube map. It is not yet agreed. Next: review it with the user and resolve its open choices (latent resources, read-back as dimension or method, how far chronology may bend, absent Players, dimension overlap, scale format). The exploration is recorded in [research/cross-domain-research.md](research/cross-domain-research.md), with the full exchange in [research/conversation-transcript.md](research/conversation-transcript.md). The starting prompt for experiments is undecided; the agent suggested `prompts/summary/experiments/combined-1346/`.
