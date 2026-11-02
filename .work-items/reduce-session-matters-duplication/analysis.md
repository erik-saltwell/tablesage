# Duplication Analysis: Brandonsford Sessions 001–004

Analysis performed 2026-10-29 against the four Brandonsford Sessions in the deployment workspace (`deployment/campaigns/Brandonsford/00N/post_session_matters.json` and the rendered `summary.md`). All four were produced by the same regeneration run on 2026-10-28 (21:29–21:46), so they are directly comparable. Those outputs will be overwritten by later regenerations; the quoted bullets below are the durable record of what was observed.

## Method

- **Within a Session only.** Open Matters intentionally carried forward between Sessions are not counted.
- **Weighted by what the reader sees.** The Session Summary shows only item titles plus Current Position and Present Danger text, so title-level restatement is the visible problem. Repetition confined to detail fields is noted separately.
- **Restatements, not shared subjects.** Each entry in an offending cluster was marked either as restating another entry or as adding a distinct fact. Sharing a subject alone does not make an entry a duplicate (see the rubric's Information preservation dimension). "Partial" means the entry adds a small amount but is mostly repetition.
- **Patterns are defined by category shape** (which category restates which, and what is restated), not by topic. Shapes seen in only one Session are recorded as candidates.

## Worst Offenders

**1. Session 003: the undead skeleton (6 bullets)**
- Development: "A huge undead skeleton with a greatsword blocked the doorway of Sir Brandon's tomb." Original.
- Present Danger: "A seven-foot brown skeleton in rusted armor and a mustachioed death mask stands in the tomb's doorway, dragging a huge greatsword…" Restates the Development, adding physical description.
- Goal Impediment: "A huge undead skeleton with a greatsword roams the Barrow Mound. It stands in the way of clearing the mound's evil for the goblins." Partial; adds only the link to the goblin Goal.
- Brewing Trouble: "The huge undead skeleton in the tomb doorway may attack the party." Restates the Present Danger.
- Brewing Trouble: "The undead skeleton may kill more Free Goblin Society members in the Barrow Mound." Partial; adds goblins as victims.
- Mystery: "Why does a huge undead figure with a greatsword roam the Barrow Mound?" Distinct.

**2. Session 004: metal from the Dwarven mine for Warwick's mithril shirt (7 bullets)**
- Development: "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." Original.
- Goal: "Bring metal from the Dwarven mine back to Warwick the smith." Restates the Development.
- New Asset: "Warwick's mithril chain shirt, lent to the party." Partial; adds that it is a loan.
- Opportunity: "The cave-in at the Dwarven mine looks diggable. If the party digs through it, they could reach metal for Warwick." Partial; mirrors the Goal Impediment, and the Development "Dunk dug into the Dwarven mine's cave-in…" shows digging already under way.
- Distinct: the Goal Impediment "A cave-in seals the Dwarven mine entrance…", the Obligation "The party must return Warwick's borrowed mithril chain shirt", and the Development "Dunk dug into the Dwarven mine's cave-in and took a magic ring from a dead dwarf".

**3. Session 001: Quinn's fake ale shipment (4 bullets)**
- Development: "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment." Original.
- Goal: "Help Quinn get back at Bentley for 100 gold." Restates the Development.
- Opportunity: "Quinn will bring bottles for a fake ale shipment. If Sir Phidipaldi fills them with water and makes a show of delivering them, they could see who takes Quinn's ale." Mostly restates the plan; adds its purpose.
- Mystery: "Who or what empties Quinn's ale at the Golden Egg every night?" Distinct.

**4. Session 002: Dr. Uriah's promise to Father William (3 bullets)**
- Development: "Dr. Uriah promised Father William to do penance at the Barrow Mound and to donate 10 gold for its upkeep." Original.
- Obligations: "Dr. Uriah must give penance at the Barrow Mound for Father William" and "Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep." Together they restate the one Development, split in two.

**5. Session 002: the dragon's scales (2 bullets)**
- Revelation: "George says arrows and swords cannot pierce the dragon's scales, and one poisonous bite kills."
- Goal Impediment: "George says nothing pierces the black dragon's scales. Arrows and swords have all failed against them." Near-verbatim restatement.

**Smaller single restatements:** Lady Hilda (001, Development and Opportunity), Eric's bounty (001, Development and Goal), Dunk and Ingrid (002, Development and Obligation), the goblin deal (003, Development and Goal), returning the robes (004, Development and Goal), Sir Alfred (004, Development and Brewing Trouble).

**Restatements per Session:**

| Session | Restatements | Partial |
|---|---|---|
| 001 | 4 | 0 |
| 002 | 4 | 2 |
| 003 | 4 | 1 |
| 004 | 3 | 4 |

## Patterns

Each established pattern has its own work item, which carries its full evidence. P6 overlaps P1, P2 and P5 (see [Cross-Pattern Observation: Open Bargains](#cross-pattern-observation-open-bargains)):

| Pattern | Shape | Sessions | Work item |
|---|---|---|---|
| P1 | A commitment made this Session is restated as a Goal or Obligation | 001, 002, 003, 004 | [.work-items/matters-dup-commitment-goal-obligation/](../matters-dup-commitment-goal-obligation/) |
| P2 | An offer or plan is restated as an Opportunity | 001, 002, 004 | [.work-items/matters-dup-offer-opportunity/](../matters-dup-offer-opportunity/) |
| P3 | A Revelation is restated as a Goal Impediment | 002, 004 | [.work-items/matters-dup-revelation-impediment/](../matters-dup-revelation-impediment/) |
| P4 | One threat spreads across Present Danger, Brewing Trouble and Goal Impediment | 003, 004 | [.work-items/matters-dup-threat-categories/](../matters-dup-threat-categories/) |
| P5 | A deal's gain is restated as a New Asset (weak) | 002, 004 | [.work-items/matters-dup-deal-gain-new-asset/](../matters-dup-deal-gain-new-asset/) |
| P6 | An open, two-sided bargain is restated in several categories at once | 001, 002, 004 | [.work-items/matters-dup-open-bargain/](../matters-dup-open-bargain/) |

## Cross-Pattern Observation: Open Bargains

Added 2026-10-29 as an observation across P1, P2 and P5, then filed as pattern P6 with its own work item, [.work-items/matters-dup-open-bargain/](../matters-dup-open-bargain/), at the user's direction the same day. The section heading is kept so existing links still resolve.

**Items that fall into more than one pattern:**

| Item | Patterns | What restates it |
|---|---|---|
| Session 001 Development: "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment." | P1 + P2 | Goal "Help Quinn get back at Bentley for 100 gold." and the Opportunity "Quinn will bring bottles for a fake ale shipment…" |
| Session 002 Development: "Dunk agreed to help Ingrid drug Warwick so she can watch him sleep…" | P1 + P5 | Obligation "Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion." and the New Asset "Ingrid's work on a sleeping potion for Dunk." |
| Session 004 Development: "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." | P1 + P5 | Goal "Bring metal from the Dwarven mine back to Warwick the smith." and the New Asset "Warwick's mithril chain shirt, lent to the party." |
| Session 004 Opportunity: "The cave-in at the Dwarven mine looks diggable…" | P2 + candidate | Restates the Development "Dunk dug into the Dwarven mine's cave-in…" and mirrors the Goal Impediment "A cave-in seals the Dwarven mine entrance…" |

**What these items share:**

- **They are two-sided bargains.** Each multi-pattern Development is an exchange in which the party agrees to do something in return for something: help for 100 gold (Quinn), help drugging Warwick for the potion (Ingrid), metal for the shirt (Warwick). A bargain has several sides, and each fits a different category: the agreement is a Development, the task is a Goal or Obligation, the way to carry it out is an Opportunity, and what the party receives is a New Asset. Each category picks up its side but restates the whole deal in its title. The single-pattern P1 cases are bargains too (the goblin deal, Uriah's penance for Father William's help, the robes), with fewer sides showing.
- **They were unfinished when play stopped.** None of them had been resolved by the end of the Session. Completed events, such as catching Naggeneen, rescuing Brother Dirk and looting the tomb, appear once as a Development only. Something still open qualifies for every forward-looking category as well as being something that happened. P4 shows the threat-side equivalent: the Session 003 skeleton was standing in the doorway when play stopped and appears in every threat category.

An open bargain, unfinished and with several sides, is the most susceptible kind of item seen. This may bear on whether P1, P2 and P5 are handled separately or together.

**Limits:**
- The suspected cause, that each category is produced separately and finds the same bargain from its own angle, has not been checked against the generation code.
- The observation rests on three Developments.
- Not every open bargain repeats: Lady Hilda's open offer appears only as a Development and an Opportunity, and Drop Dead Ned's and Farmer Gill's offers appear only as Developments.

## Candidates Not Given Work Items

Seen in one Session each; not opened as work items (user decision, 2026-10-29).

- **Goal Impediment mirrored by an Opportunity:** Session 004's cave-in. The obstacle ("A cave-in seals the Dwarven mine entrance…") and the way around it ("The cave-in at the Dwarven mine looks diggable…") are phrased as two items, and the Opportunity adds little.
- **Mystery left open beside a Revelation that largely answers it:** Session 004 asks "What happened to Grimny and the other dwarves at the Dwarven mine?" while the Revelation "Grimny's ghost believes his greedy brother Bral killed him…" is marked as substantial Mystery progress. This may be staleness rather than duplication.

## Within-Category Splits

One source item split into several items in the same category: Session 002's single promise became two Uriah Obligations, and Session 003's single skeleton became two Brewing Troubles. The intent targets repetition across categories, and the earlier [Remove duplicates in Post-Session Matters](../post-session-matters-dedup/) item ruled out within-category repetition. Whether splits are in scope is unresolved; they were not given work items.

## Seen but Not Counted

- **Open Matters carried forward between Sessions:** the Lady Hilda Opportunity (001–003), the scales Goal Impediment (002–004), the Uriah Obligations (002–004) and the dragon Brewing Trouble (002–004). Carrying forward is intended.
- **Stale entries:** Uriah's penance at the Barrow Mound is still listed after the party went there; Squints' share is still listed after the treasure was traded; the Sir Alfred threat in Session 004 is over but still listed under "Meanwhile". Staleness is a separate defect.
- **Detail-field repetition:** the sword news in Sessions 003 and 004 is copied into the details of the Goal Impediment, the Brewing Trouble and the Goal. The Summary does not show it.
- **Overlaps judged distinct:** catching Naggeneen (an event) versus learning he is the thief (a fact) in 002; Squints joining (a gain) versus his treasure share (a price) in 002, and similarly Lady Hilda and Malzazarik joining versus their payment in 004; Quinn's plan versus the ale Mystery in 001.

## Limits

Four Sessions from one campaign is a small sample. P1 is well supported; P3, P4 and P5 rest on two Sessions each.
