---
name: "Table Recap: sentence case for item text"
status: complete
---

# Table Recap: sentence case for item text

Write item text in sentence case instead of Title Case. Headline-style bullets such as "Sir Phidipaldi Stripped Sir Brandon's Armor From His Corpse as the Party Looted the Tomb" read like newspaper headlines and are harder to scan and paraphrase. Section headings are out of scope.

Affected in the Summary: the Previously and You learned bullets. The Table Recap's "Last time" and "You learned" sentences have the same problem. Evidence: [001](../../deployment/campaigns/Brandonsford/001/table_recap.md), [002](../../deployment/campaigns/Brandonsford/002/table_recap.md), [003](../../deployment/campaigns/Brandonsford/003/table_recap.md), [004](../../deployment/campaigns/Brandonsford/004/table_recap.md).

Open question: fix at the source (the Developments/Revelations prompts that produce the headlines) or normalize in rendering. Fixing it at the source would cover both artifacts; a renderer can't reliably sentence-case text containing proper nouns.

Table Recap generation is currently paused until its replacement is designed (see the [Deterministic Session Summary specification](../deterministic-table-recap/specification.md)); apply this to that replacement design rather than to the old model-generated recap.

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28, treating them as material a GM uses at the table. The user prefers short, paraphrasable bullet lists over read-aloud box text.

Resume: no quality rubric exists yet; define one before ideating or planning.

Closed without implementation on 2026-10-28 at the user's direction.
