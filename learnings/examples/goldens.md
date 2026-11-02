# Goldens and the User's Own Edits

The most direct preference evidence: text the user wrote or edited by hand. Conventions are in [README.md](../README.md).

Sources:
- the user's original handmade file and its revisions, kept by Syncthing in `~/proj/tablesage/docs/.stversions/delete_me/` (R-10)
- the review of it in SRC-01
- the Session 001 and 002 goldens in `~/data/tablesage_summary_test/artifacts/session_*/golden/`

Later golden changes were made by the assistant at the user's request; those are recorded with the matter they affect (for example EX-010, EX-011).

---

### EX-049 The user's first handmade Campaign Matters
- Verdict: good (the original target)
- Scope: all matters
- Session / run: Brandonsford Session 002, hand-written on 2026-10-17 and 2026-10-18 (Syncthing versions `Untitled~20261017-195027.md` through `HandmadeCampaignMatters~20261018-111230.md`)
- Source: R-10, SRC-01 (2026-10-18T17:12Z)

**The text** (verbatim, first full version, `HandmadeCampaignMatters~20261018-105838.md`, typos included):
> ## Mysteries
> where / what is the treasure?
> How is this dragon related to the original one sir Brandon was supposed to have killed?
> What is going on with the fearies?
> What happened to gill's sons?
> Why does Warwick stuff his house with lucky charms?
> Why have supply shipments stopped?
> Who is stealing the booze from the golden egg?
>
> ## goals
> Fine the treasure in brandonsford
> Kill the dragon and collect your 1000 gold
>
> ## obligations
> - give squints a share of your loot and 3 adventuring tips a day
> ## threats
> - the dragon will soon be able to fly
> - the town is running out of supplies
>
> ## opportunities
> If you get Brendan's sword, it can help slay the dragon.
> If you can steal Warwicks chain mail, it will protect you against the dragon
> If you get the portion from ingrid, it will keep Warwick asleep while your steal the chain mail

**Added by the user 15 minutes later** (verbatim, from the `~111230` diff):
> If you hire the other adventurers they can help you kill the dragon
> If you free Naggeneen, he'll give you his pot of gold or a secret
> ## Revelations
> Sir Brandon's sword location is known
> Naganeen the clurichen was the one stealing booze from the Golden Egg
> The dragon has a poisonous bite and spits sulfur, and no weapon has pierced its scales.
> Ingrid loves Warwick the Smithy and has been leaving items by his bed.
> Eric the Reeve may not have the money.

**Context needed to judge it:** the assistant's comparison with the generated outputs of the time (SRC-01): "Entries: 15 vs 19–21. Words: 145 vs 650–730." The user's file is "mostly mysteries; the outputs are mostly opportunities." Mysteries were written first: the 2026-10-17 note contains only that section.

**What it shows:**
- About 10 words per entry, and one point each.
- **Mysteries come first** and include planted oddities (the charms, the fairies) and situations that went quiet (Gill's sons, the shipments).
- Goals are the party's ends only.
- Opportunities use "If you X, Y".
- Threats are clocks ("will soon be able to fly", "running out").
- Doubt goes on the premise ("supposed to have killed", "may not have the money").
- One subject (the dragon) appears under several categories.

**Spot it:** set a new output beside this file. Is each entry about this short, in this voice, and in the category whose question it answers?

**Outcome:** became the Session 002 golden after the review in SRC-01. Several choices later changed:
- the window and the potion became child Opportunities (EX-040)
- Revelations narrowed (EX-011)
- Opportunities need a Goal (EX-041)
- the treasure Mystery is filtered out (EX-017)
**Links:** [PREF-004](../preferences.md#pref-004), [PREF-007](../preferences.md#pref-007), [PREF-033](../preferences.md#pref-033)

---

### EX-050 A threat worded so it does not overstate what is known
- Verdict: good (user's intent; final wording agreed)
- Scope: brewing-troubles, present-matters
- Session / run: Session 002 golden
- Source: SRC-01 (2026-10-18T18:26Z–18:33Z)

**The user's draft** (verbatim, as quoted in the review): "may be in the first north of town". The review noted: 'Besides the typo ("forest")…'

**The reviewer's suggestion:** *"The giant you robbed of Brother Dirk is awake, and his cottage is on your road north."*

**User's reaction** (verbatim):
> I understand your point. My reason for saying maybe is that I wanted a statement that highlighted the threat and danger without overstating what we know. I guess we could also say something like, the giant is angry that the party stole its food.

**Final golden** (verbatim):
> The giant is angry that you stole his dinner, Brother Dirk. His cottage is on your road north.

**In the same golden:** Present Danger is "- None." The user accepts an empty danger section when nothing is threatening the party right now.

**Why it is good:** it states what is established (he is angry; where he lives) and lets the danger follow, without inventing a pursuit.

**Spot it:** a threat names what is actually established and adds no predicted action.
**Links:** [PREF-031](../preferences.md#pref-031), [PREF-037](../preferences.md#pref-037)
