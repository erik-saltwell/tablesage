# AI-Assisted Reincorporation Planning

## Status

Current concept and plan of record. This document captures the product direction
and decisions agreed during workshop and follow-up design discussion. It does
is implemented following explicit implementation approval. The product workflow
below records the agreed scope.

## Purpose

Help a game master turn Campaign memory into useful opportunities for an
upcoming Session.

The difficult planning task this feature addresses is reincorporation: bringing
an established Campaign element back into play so that it acquires new meaning,
gains new utility, expresses a consequence of player action, or creates an
earned emotional or thematic callback. The feature uses the Campaign's recorded
history to notice promising elements that a GM may not recall while preparing.

The feature is a **reincorporation assistant**, not a general-purpose plot or
Session generator. The GM remains responsible for the Campaign's forward motion
and supplies a brief indication of what might happen next. The assistant finds
ways that prior play could become relevant to that possible future.

Its core promise is:

> Tell me what might happen next, and I'll show you what from the Campaign could
> matter again.

The feature launches from Campaign Detail's **Generate Opportunities** secondary
action. Unlike the
[Campaign-Aware “Previously On” feature](../campaign-aware-previously-on/proposal.md),
its output is private GM preparation rather than a player-facing recap.

## Core experience

1. The GM enters a required brief free-text prompt about what they expect may
   happen in the upcoming Session. One or two sentences are sufficient. The
   Campaign recap's ending situation is displayed for context.
2. The assistant uses the complete Campaign Scene Recap, including its ending
   situation, together with the GM's prompt to generate up to five concise,
   evidence-backed reincorporation opportunities.
3. The GM reads the pitches on screen. The prompt remains editable, allowing
   the GM to revise the direction and generate a replacement set on the same
   screen. Displayed results are replaced only after generation succeeds;
   a failed attempt preserves the previous results.
4. Save exports the entire displayed set as Markdown, including the GM prompt
   used to generate that set. There is no per-opportunity selection step.

The assistant proposes ingredients, tensions, and openings. It does not outline
a plot, prescribe Scenes, or predict what the players will choose.
The initial pitch is the complete offering: the GM needs seeds and develops
them independently. There is no expansion or alternative-treatment workflow.

## Campaign input and readiness

Every Session in the Campaign must have a current, valid, complete Scene
Breakdown before generation. Missing, stale, invalid, or incomplete breakdowns
block generation; the workflow does not silently omit Sessions or substitute
other artifact types. Scene Breakdowns supply the Campaign evidence used to
ground opportunities and assess freshness and dormancy.

Use the existing complete **Campaign Scene Recap**, a read-only view of all
Scenes in Campaign order bracketed by the Campaign's starting and ending
situations. This is distinct from the selective per-Session `recap_summary.md`.
See the [Scene Breakdown specification](../../../.work-items/scene-breakdown-artifact-contract/specification.md#campaign-aware-previously-on-export)
for its composition and readiness checks.

The model receives the recap's ending situation as established context and the
GM prompt as a possible future direction, not evidence that future events have
occurred. The prompt is required even though the ending situation is available:
it supplies relevance without requiring a detailed Session plan.

The complete recap must fit within the model's context for the initial version.
If it does not, generation reports that the Campaign is too large for this
version. History selection and further compression are out of scope; context
capacity is not expected to be a practical problem initially. Retaining all
Scenes avoids selecting away the minor details this feature aims to rediscover.

## Opportunity set

Each generation targets up to five opportunities. Five is a ceiling, not a
quota: return fewer when the evidence does not support enough strong pitches.
The set may contain:

- **Single-element opportunities**, each returning one established
  Campaign element; and
- a **connection opportunity**, which finds a useful intersection between two
  established Campaign elements.

A connection must earn its place; there is no required mix or reserved
connection slot. A fixed quota would encourage filler and strained relationships.

The connection opportunity should not manufacture an arbitrary secret
relationship merely to create a twist. It must identify the status of the
proposed bridge between its two source elements:

- already established in the Campaign;
- a reasonable inference from established facts; or
- a new possibility offered for the GM's consideration.

The set should be deliberately varied rather than simply containing the five
highest-ranked candidates of the same kind. Relevant material may include
people, factions, relationships, player decisions, commitments, locations,
objects, discoveries, consequences, or emotional and thematic moments.

Open threads are important candidates, but they are not the feature's complete
scope. Apparently resolved or minor material can support powerful
reincorporation when later context gives it new meaning or utility.

## Opportunity presentation

Each opportunity has a short title and two brief parts, **From the Campaign**
and **Opportunity**, targeting around 60–100 words total per pitch. These parts
separate remembered Campaign material from creative invention without extra
labels or formal source citations.

### From the Campaign

- the established element or elements;
- what happened and why the material may be ripe for return.

Neither the screen nor saved Markdown includes formal Session or Scene
citations. Grounding remains required: briefly recalling the established
material lets the GM recognize the callback.

The grounding must preserve the source's uncertainty. A player suspicion,
rumor, or unresolved interpretation must not be restated as an established
fact.

### Opportunity

- a concrete way the element could intersect with the GM's expected upcoming
  situation; and
- a concise, flexible opening through which it might naturally enter play.

The opening makes the preparation portable. It should remain usable through
multiple player approaches and must not depend on a predetermined player action
or Scene outcome. If no opening arises during play, the GM should not need to
force the reincorporation.

The design optimizes for helping the GM find one useful seed. Development beyond
the concise pitch belongs to the GM.

## Choosing ripe material

“Ripeness” is a qualitative model judgment, not a visible numeric score or a
rigid checklist. The model should consider:

- **Player authorship:** The element arose from a player decision or invention.
- **Player investment:** Players showed curiosity, emotion, or sustained
  attention.
- **Present relevance:** It intersects naturally with the GM's upcoming
  situation.
- **Transformative potential:** It could gain new meaning or utility.
- **Dormancy:** Enough time has passed for its return to feel meaningful.
- **Specificity:** Players are likely to recognize the callback.
- **Freshness:** The element has not already been reincorporated repeatedly.

The assistant should use these considerations to form a strong and diverse set,
not mechanically select items with the largest apparent scores. Each
opportunity's explanation should state its strongest reasons for being ripe in
natural language.

When developing opportunities, the model may consider whether a returning
element could:

- help the players;
- complicate matters;
- reveal a consequence of earlier play;
- deepen a relationship; or
- create thematic or emotional resonance.

These are non-exhaustive creative lenses, not categories the output must fill or
labels it must display. The model may choose another treatment when it fits the
Campaign better. There is deliberately no “surprise me” lens; freedom to find a
better treatment is already part of the task.

## Ephemeral results and Markdown saving

The workflow is ephemeral. Markdown saved explicitly by the GM is its only
persisted planning output. There is no internal suggestion-history table,
opportunity lifecycle, or matching of past suggestions against later play.
The GM does not mark suggestions as kept, dismissed, deferred, or reincorporated.

Save includes the whole displayed set and its generating prompt. With at most
five brief pitches, selection controls add little value; the GM can edit the
Markdown afterward. Revising and regenerating replaces the set without creating
an in-app result history.

Freshness and dormancy are judged solely from recorded Campaign events. Repeated
generation may therefore suggest similar opportunities when the Campaign
history and upcoming situation have not changed; this is acceptable for the
initial version.

Generated opportunities and saved Markdown remain speculative preparation and
are not sources of Campaign evidence for future generation.

## Product principles

- **Campaign memory in service of GM agency:** AI notices and proposes; the GM
  decides what matters and what becomes true.
- **Reincorporation over plot generation:** The feature enriches likely future
  play with established material rather than inventing a Session trajectory.
- **Evidence before invention:** Suggestions expose their historical grounding
  and distinguish facts, uncertainty, inference, and new possibilities.
- **Player impact matters:** Player-authored decisions and their consequences
  are especially valuable sources.
- **Surprising but earned:** The result set balances obvious threads with
  credible deep cuts from minor or apparently completed moments.
- **Portable preparation:** Opportunities survive deviations from the GM's
  expected course and never need to be forced into play.
- **Small, useful output:** Up to five differentiated pitches, with no filler
  to meet a quota, keep preparation quick to scan.

## Implementation choices

The screen shows ending context, editable input, and read-only Markdown results.
Ctrl-G generates; Ctrl-S saves; Escape returns to Campaign Detail. Save defaults
to `opportunities.md` in a home-directory file picker and requires a Markdown
destination outside managed Campaign data. Existing-file replacement requires
confirmation. Saving stays on the screen; errors preserve results for retry.

Generation uses `llm_model_high` with deployed `opportunities_timeout` (default
600 seconds). Structured validation enforces nonempty pitch fields and at most
five results; the 60–100-word target is a prompt instruction. An empty result
shows a message suggesting prompt revision. Provider context-limit failures
report that the Campaign is too large; history is never silently truncated.

Implementation: [application use case](../../../packages/tablesage-application/src/tablesage_application/opportunities.py)
and [TUI screen](../../../apps/tablesage-tui/src/tablesage_tui/screens/opportunities.py).
