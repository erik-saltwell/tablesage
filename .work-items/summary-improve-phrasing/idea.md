# Improve Phrasing: Idea

Workshop result from 2026-10-28 for making the Session Summary (`summary.md`) sound natural when a GM uses it aloud at the table. The problems it addresses and the four settled phrasing decisions are recorded in [item.md](item.md). This document records the mechanism and headings agreed in the workshop. No quality rubric was approved; the workshop judged the idea against working dimensions (see below).

> **Revised 2026-10-28 (user decision, after the first implementation).** The separate phrasing pass described under "Mechanism" was implemented and then removed. In the first live run, two of four Sessions fell back to Title Case because the model returned only the first section. The user then chose instead to embed the read-aloud guidance in each Matters prompt that produces Summary text, with the Summary staying a deterministic template render. This reverses the "Matters record stays unchanged" decision: stored Matters are now second-person, sentence-case and fitted to their headings. Reuse of the previous Session's wording, the phrasing record and the fallback no longer exist. The phrasing rules and headings below still apply. The Mechanism, Rejected and Accepted risks sections are kept as history.

> **Revised again 2026-10-28 (user decision).** The second-person rule was reverted: Matters text refers to the party as "the party" again, and individual characters by name. Sentence case, bullets fitted to their headings, and the heading set remain.

## Intended effect

A GM can glance at the Summary and say a heading followed by its bullets without the result sounding like box text: one voice, natural spoken lead-ins, sentence case, and bullets that read cleanly after their heading. This should not damage the Post-Session Matters record that later extractors, future Sessions and any future Table Recap read.

## Phrasing rules (settled; detail in [item.md](item.md))

- Second person ("you") throughout. Bullets about one character keep that character's name ("Dr. Uriah must give penance…").
- Headings are phrased to be read verbatim as spoken lead-ins.
- Headings and bullet text use sentence case, not Title Case.
- Each bullet is a complete, standalone phrase starting with a capital letter that reads naturally after its heading, without repeating or clashing with it: under "You learned", "The smith is the cult leader", not "You learned that…". Bullets are deliberately not grammatical continuations such as "that the smith is…".
- Keep the existing "why it matters" clauses on items (user decision, for now).

## Headings (settled)

| Section | Current heading | New heading |
|---|---|---|
| Developments | Previously | Last session... |
| Revelations | You learned | You learned |
| New Assets | You acquired the following resources | You gained |
| Goals | Your goals remain | Your goals |
| Goal Impediments | Standing in your way | Standing in your way |
| Opportunities | Openings | What could help |
| Mysteries | Remaining Questions | Still unanswered |
| Obligations | Commitments | Promises and debts |
| Brewing Troubles | Meanwhile | Meanwhile |
| Current position | As we return | As we return |
| Present danger | The immediate danger | The danger right now |

"Last session..." is sentence case with the trailing ellipsis, as the user specified. "Promises and debts" must also cover obligations owed to the party (for example, Squints' treasure pick). Renaming the danger heading belongs to this item; what qualifies as a present danger belongs to the separate [immediate-danger item](../summary-immediate-danger/). Headings currently live in [session_summary.j2](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2).

## Mechanism (settled)

**Phrasing pass.** Add one LLM step between Post-Session Matters and `summary.md`. It receives the assembled items with their final headings and rewrites each item for the table, following the phrasing rules. It produces exactly one output per input item, matched by ID and in the same order, and adds no facts. Code validates the response; if validation fails, the whole Summary falls back to the original Matters text.

- *Why:* Matters items are the canonical record consumed by later extractors and future Sessions, so phrasing them for one heading would push presentation into data. The Matters prompts also reason in neutral third person, and the Developments prompt currently asks deliberately for title-case headlines. One prompt that sees headings and bullets together is more consistent than teaching the style to ten selection-focused prompts. It also resolves the earlier open question of how each Matters prompt would learn its heading.
- *Accepted cost:* the Summary is no longer assembled without model calls, which reverses that part of the [Deterministic Session Summary contract](../deterministic-table-recap/specification.md). It adds an LLM call, cost and run-to-run variation.

**The Matters record stays unchanged.** Post-Session Matters and the individual Matters keep their current neutral third-person text and casing.

**Reuse last Session's wording for unchanged items.** When an item's ID and source text match the previous Session's Post-Session Matters, reuse the previous Summary's phrased bullet instead of rewriting it. Only new or changed items go through the phrasing pass.

- *Why:* ongoing items (the dragon bounty goal, "Why have shipments stopped?") read identically week to week, there are fewer chances for drift, and the call shrinks over time. It also lays groundwork for the separate [new/changed/ongoing item](../summary-new-changed-ongoing/).
- *Accepted cost:* the Summary now depends on the previous Session's Summary, so regenerating one Session can affect the next one's wording. Stored wording must be invalidated when the headings or the phrasing prompt change. A badly phrased bullet carries forward until its source item changes.

**Option A, not B.** The phrasing pass rewrites `summary.md` itself. The user considered and declined an alternative in which the Summary stays assembled without an LLM and the phrased output becomes the Table Recap. The [Table Recap phrasing items](../table-recap-heading-listenability/) remain separate.

## Rejected

- **Changing the voice and casing inside the ten Matters prompts.** Replaced by the phrasing pass, for the data-safety and consistency reasons above.
- **Per-item validation and fallback** (checking that each rewrite keeps its source's proper nouns and numbers, and falling back item by item). The user judged it over-engineering for this change; whole-Summary fallback stays.
- **Letting GM edits to phrased bullets carry forward.** Considered at the end and not pursued: it would need bullets mapped back to item IDs and a Summary editing flow that doesn't exist. Revisit only if bad wording visibly lingers in practice.

## Accepted risks

- Subtle factual drift inside a rewrite (a changed amount or name, or "may" hardening into "will"). Only missing or extra items are caught.
- An occasional whole-Summary fallback to the old Title Case, mixed-voice text.

## Working dimensions used in the workshop

Not an approved rubric; recorded so later assessment can start from them.

- **Sounds right aloud:** heading followed by bullet sounds natural when spoken.
- **Scannable:** the GM finds the point at a glance.
- **Safe for the data:** facts and later steps are not harmed.
- **Consistent:** the style holds across every category and across Sessions.

## Open for planning

- The phrasing prompt's wording, input/output schema and validation rules.
- Where reused phrasings are stored and how they are invalidated (heading changes, prompt changes, previous Session regenerated).
- How a fallback is recorded in the generation record.
- How the new step fits the artifact dependency and freshness rules, and the existing regeneration and `tablesage regenerate-session-summary` paths.
- Settings for the new LLM call, following the project's settings rules.
