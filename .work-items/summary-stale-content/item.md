---
name: "Session Summary: remove stale, duplicated and inconsistent content"
status: complete
---

# Session Summary: remove stale, duplicated and inconsistent content

Make sure carried-forward content is current and stated once:

- Settled situations remain listed. Session 004's Summary Meanwhile says "The giant undead skeleton is about to attack the party in Sir Brandon's tomb", although the same Session's Previously says the party left Sir Alfred incapacitated.
- Once something has a name, use it consistently ("Sir Alfred" vs. "the giant undead skeleton").
- One fact can appear in several sections. Session 003's Summary mentions the skeleton in the doorway in Previously, As we return, Meanwhile and The immediate danger. It should appear once, in the most relevant section.
- Commitments never close. Dr. Uriah's penance and 10-gold donation carry forward from 002 onward with no sign of whether they were fulfilled; Session 004's Table Recap still lists Sir Phidipaldi's fake ale delivery for Quinn.

Fulfilled or settled items should simply drop out. The user explicitly does not want a "Resolved" section announcing them.

Evidence: [001](../../deployment/campaigns/Brandonsford/001/summary.md), [002](../../deployment/campaigns/Brandonsford/002/summary.md), [003](../../deployment/campaigns/Brandonsford/003/summary.md), [004](../../deployment/campaigns/Brandonsford/004/summary.md). The root cause is probably upstream carry-forward in Matters generation (Brewing Troubles, Obligations) rather than in rendering; see the [Post-Session Matters specification](../post-session-matters/specification.md). Coordinate with the matching Table Recap item.

Origin: GM-perspective review of the Brandonsford Session 001–004 outputs on 2026-10-28, treating them as material a GM uses at the table. The user prefers short, paraphrasable bullet lists over read-aloud box text.

Closed 2026-10-28 at the user’s explicit request. This closure does not assert that the issues above were implemented or verified.
