---
name: "Table Recap: spoken presentation from Session Summary"
status: complete
---

# Table Recap: spoken presentation from Session Summary

Generate the Table Recap in a separate LLM step using the deterministic Session Summary as input. Preserve all Summary content, reframe party references in the second person, keep the event and reference sections as bullets, and combine the current situation and any immediate danger into one brief closing passage under “As we return”, without a separate danger heading.

The [intent and approved quality rubric](intent.md) records the settled behavior and its rationale. The rubric values player orientation and spoken usability. This replaces the original proposal to split a short read-aloud core from GM-only reference; the folder is retained for continuity. The Session Summary itself remains unchanged.

General clarity improvements belong upstream and are captured separately in [Matters: clearer wording for Summary and Table Recap](../matters-plain-language/item.md). The Table Recap step focuses on second-person phrasing and the closing presentation. See the [workshop assessment](evaluations.md) for expected benefits and remaining uncertainty.

Table Recap generation is enabled under the [Spoken Table Recap contract](specification.md). The [Session Summary contract](../deterministic-table-recap/specification.md) remains deterministic. Second-person phrasing also overlaps the separately tracked [Table Recap: phrase in second person](../table-recap-second-person/item.md); that item's status has not been changed or merged here.

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28. The user prefers short, paraphrasable bullet lists over long read-aloud passages. Historical output examples: [001](../../deployment/campaigns/Brandonsford/001/table_recap.md), [002](../../deployment/campaigns/Brandonsford/002/table_recap.md), [003](../../deployment/campaigns/Brandonsford/003/table_recap.md), [004](../../deployment/campaigns/Brandonsford/004/table_recap.md).

Completed 2026-10-28. The Summary-based LLM producer, combined closing passage, second-person wording, regeneration UI/CLI, downstream freshness and Generate Artifacts completion are implemented. See [progress.md](progress.md) for verification and limitations, and [evaluations.md](evaluations.md) for qualitative rubric findings. A [live representative output](verification/table-recap.md) is saved for review. No live Campaign outputs were replaced, and the separate upstream wording item remains captured for later.
