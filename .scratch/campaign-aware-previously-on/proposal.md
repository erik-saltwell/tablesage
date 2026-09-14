# Campaign-Aware “Previously On” Export

## Status

Fleshed-out feature design. This document records the agreed direct-recap
workflow and its boundaries. It does not authorize implementation.

## Purpose

Give a GM who already has a reasonable idea of the upcoming Session a fast way
to create a television-style “Previously on…” recap. The recap may draw Scenes
from anywhere in the Campaign, restoring memories that could matter next while
also establishing where play will resume.

The result presents selected past Scenes without explaining why they were
chosen. Players may recognize that an old moment is likely to matter, but the
recap does not reveal the connection.

TableSage's [Scene Breakdown specification](../../specs/scene-breakdown.md)
already preserves every Scene in each Session for Campaign-scale reading. This
feature consumes those records without changing them.

## Product boundary

This is an external export workflow, not part of the Session artifact pipeline:

- It launches from Campaign detail.
- It reads Campaign Scene Breakdowns and the Campaign glossary.
- Its working state is ephemeral.
- It writes a GM-chosen Markdown file outside managed Campaign data.
- It does not create or update a Campaign or Session record.
- It does not replace `recap_summary.md`, affect artifact freshness, or feed a
  later Session Summary.

Campaign detail receives a separate **Create Previously On** action. The
existing **Prepare Next Session** action remains reserved for future
AI-assisted planning.

## Experience principles

- **Montage, not summary:** The result should feel like selected clips from
  earlier episodes.
- **Future relevance, not recent chronology:** An older Scene may be more useful
  than an event from the latest Session.
- **Show connections; do not explain them:** The recap never states why an old
  Scene matters now.
- **The GM is the editor:** AI proposes; the GM can select any recorded Scene.
- **Campaign history is authoritative:** Recap material remains grounded in
  Scene Breakdowns.
- **Future plans are private:** Upcoming-session notes guide scouting but never
  reach the recap editor.

## Preconditions

Every Session in the Campaign must have a current, valid, complete Scene
Breakdown. A missing, invalid, incomplete, or stale breakdown blocks the
workflow.

The **Create Previously On** action remains visible and available when the
precondition fails. Invoking it shows a blocking message that names the
affected Sessions and directs the GM to **Regenerate All Outputs**. It does not
start regeneration automatically.

At least one Scene must ultimately be selected before export.

Handling a Campaign whose accumulated Scene Breakdowns exceed the model's
context is out of scope for the initial feature.

## Workflow

```text
Campaign detail
    -> generate Campaign ingredients
    -> quick entry
    -> scout proposes Scenes
    -> GM selects from complete Scene catalog
    -> choose destination
    -> recap editor writes Markdown
    -> Campaign detail
```

### 1. Launch and generate Campaign ingredients

The GM invokes **Create Previously On** from Campaign detail. TableSage verifies
the Scene Breakdown precondition, then shows progress while an LLM reads the
Campaign's accumulated Scene Breakdowns and glossary to produce Campaign
ingredients.

The LLM may infer unresolved threads, plausible nearby NPCs, and active
pressures from recorded Scenes. It must ground every ingredient in source
Scenes and must not invent encounters or future developments. The glossary is
spelling and identity orientation, not evidence that an event occurred.

If ingredient generation fails, TableSage shows the error and returns to
Campaign detail. Quick entry does not open in a degraded state.

### 2. Quick entry

Quick entry is a split-pane screen.

The left pane contains:

- the editable starting situation; and
- a free-form field asking what might happen next Session.

The right pane contains four fixed ingredient sections:

1. **People & Factions**
2. **Threads & Commitments**
3. **Active Pressures**
4. **Places & Objects**

Each section shows up to five strong candidates. There is no “Show more” or
full Campaign browsing from this screen.

Every ingredient shows a short label and one-line current-state summary. A
focused detail panel exposes its supporting Sessions and Scenes. Ingredients
are immutable, source-backed suggestions: the GM may select or ignore them,
but cannot edit them. Corrections and additional context belong in the
free-form notes.

All ingredients begin unselected. Selection is binary; there are no
**Expected**, **Possible**, or other certainty states. An ingredient affects
scouting only when the GM explicitly selects it.

The GM may continue when either the free-form notes are nonempty or at least
one ingredient is selected. The inferred starting situation alone is not
sufficient input.

#### Starting situation

The starting situation is initialized directly from the latest Session's
recorded `ending_situation`; it does not require another LLM call. The GM can
edit it when the next Session will open differently. The edited value guides
the scout and later supplies the factual basis for the recap's closing
situation.

There is no intermediate or persisted **Session Outlook**. The edited starting
situation, selected ingredients, and raw GM notes go directly to the Scene
scout.

### 3. Scout relevant Scenes

The Scene-scout LLM receives:

- every Campaign Scene Breakdown;
- the edited starting situation;
- selected Campaign ingredients;
- the GM's raw upcoming-session notes; and
- the Campaign glossary as spelling and identity orientation.

It recommends the smallest set of Scenes that provides useful callbacks and
recent continuity. There is no numeric target or maximum. Any recorded Scene
is eligible, including a Scene experienced by only part of the party; the GM
owns audience and spoiler judgment.

For each recommendation, the scout returns an unambiguous Session-and-Scene
reference and a private relevance rationale. It proposes source material but
does not write the recap.

If scouting fails, quick-entry state remains intact. TableSage shows the error
and allows a manual retry.

### 4. Select from the complete Scene catalog

The selection screen presents every recorded Campaign Scene in chronological
order:

```text
Session
└── Scene
```

Sessions appear oldest to newest. Only Sessions containing scout-recommended
Scenes are initially expanded; all others remain collapsed but directly
available.

Scout recommendations are highlighted and preselected. The GM may select or
deselect any Scene. There is no hard or suggested Scene-count limit, no split
quota for older versus latest-Session Scenes, and no requirement that a Scene
from the latest Session be included. At least one Scene must remain selected.

Each catalog row shows the Scene title and a compact situation/outcome summary.
Focusing a Scene shows its complete Scene Breakdown data and, for scout
recommendations, the scout's private rationale.

The screen shows checkbox state, a selected count for each Session, and a total
selected count. It does not duplicate the selection in a separate recap-reel
panel, and the GM does not manually reorder Scenes. Selected Scenes are passed
to the editor in Campaign chronology.

The GM may return to quick entry with all quick-entry inputs preserved. Running
the scout again replaces the complete prior Scene selection with the new scout
result; it does not merge old manual choices.

### 5. Choose the export destination

The save-file dialog opens before the recap-editor call. It starts in the
user's home directory and suggests:

```text
<campaign-name>-<next-sequence:03d>-previously-on.md
```

For example, a Campaign named `Brandonsford` whose next Session sequence is
`3` suggests `Brandonsford-003-previously-on.md`. “Next sequence” uses the
same `max(sequence_number) + 1` and three-digit formatting convention as
existing Session folders; it does not use the Session UUID. The destination is
a Markdown file.

If the destination already exists, the GM must explicitly confirm replacement
before recap generation starts. Canceling the save dialog returns to Scene
selection with all state preserved.

### 6. Generate and save the recap

A separate recap-editor LLM receives only:

- the selected Scene records in Campaign chronology;
- the edited starting situation;
- the Campaign glossary as spelling and identity orientation; and
- format and style instructions.

It does not receive unselected Campaign history, ingredient cards, GM notes,
future developments, or scout rationales. This information boundary prevents
the editor from explaining why Scenes were selected or importing unapproved
history.

The editor produces the complete Markdown document. TableSage does not parse,
restructure, or validate the model's result and does not enforce word or Scene
counts. The prompt directs the model to be brief and concise.

The requested Markdown form is:

- one `# Previously On` heading;
- one unlabeled vignette for each selected Scene, in Campaign chronology; and
- one distinct closing paragraph establishing where play resumes.

The editor may rewrite the GM-edited starting situation for brevity and flow,
but must preserve its facts. Source Session names, Scene titles, and provenance
do not appear in the player-facing export.

TableSage writes through a temporary file and atomically replaces the chosen
destination only after successful generation. A provider failure leaves an
existing destination untouched, preserves the Scene selection and destination,
and permits retry. A successful write returns directly to Campaign detail; it
does not open an in-app preview, show a completion screen, launch an external
editor, or retain a resumable draft.

## Cancellation and ephemeral state

All workflow state exists only for the active flow. Leaving before a successful
save discards the starting-situation edits, notes, ingredient choices, scout
output, and Scene selection. If the GM has made meaningful changes or reviewed
Scene selections, exiting requires confirmation.

Canceling only the save-file dialog is not treated as leaving the workflow; it
returns to Scene selection without data loss.

## Advantages to capture

### Campaign-wide continuity

Old information can become meaningful again, making the Campaign feel
interconnected rather than episodic and forgetful.

### Better setups and payoffs

The GM can fairly remind players of established clues before consequences
arrive, supporting recognition without an explanatory lore dump.

### Reduced memory and blank-page burden

The latest ending state, four-part ingredient palette, and source details let
the GM react and select rather than reconstruct the Campaign from memory.

### Preservation of GM agency

AI handles Campaign recall and proposes a first cut, while the complete Scene
catalog keeps final inclusion under GM control and makes scout mistakes
recoverable.

### Emotional as well as factual recall

Scenes can restore relationships, promises, fears, betrayals, and distinctive
moments rather than only isolated facts.

### Spoiler-resistant generation

Separating the scout from the context-blind recap editor lets future plans
influence retrieval without appearing in player-facing prose.

### Familiar external workflow

The result is an ordinary Markdown file the GM can inspect and edit with their
preferred tools. It creates no new managed artifact lifecycle.

## Costs and risks to mitigate

| Cost or risk | Current response |
| --- | --- |
| Resurfacing an obscure Scene may telegraph what matters next | The scout includes genuine continuity as well as callbacks, and the GM controls the final selection. |
| Inferred ingredients may be subtly wrong | Suggestions are unselected, immutable, source-backed, and accompanied by evidence. |
| Scout suggestions may bias the GM because they arrive preselected | The complete catalog and detailed rationales make removal and replacement possible. |
| The scout may miss an important Scene | Every recorded Scene remains selectable, whether or not the scout proposed it. |
| A complete catalog may become unwieldy | Sessions are collapsible and only Sessions containing initial selections open by default; search is deferred. |
| Scene Breakdown compression may omit a decisive detail | The feature can show complete Scene Breakdown data, but richer retrieval is deferred. |
| A glossary may contain facts absent from selected Scenes | Every prompt treats it only as spelling and identity orientation, never event evidence. |
| The recap editor may invent, omit, reorder, or malformedly format content | The prompt supplies grounded Scenes and explicit instructions, but the accepted design performs no output validation and relies on external GM review. |
| The recap editor may alter the edited starting situation | It is instructed to preserve facts while rewriting concisely; there is no in-app verification. |
| Unlimited Scene selection may produce a long recap | The prompt asks for brevity; there is deliberately no count or word enforcement. |
| Every Session must have a current Scene Breakdown | A blocking message identifies affected Sessions and points to explicit Campaign-wide regeneration. |
| Ingredient generation failure prevents even notes-only use | The accepted fail-and-exit behavior keeps the screen from opening without its intended memory palette. |
| Multiple LLM stages add latency and model cost | Progress is shown at launch; later calls preserve user state on failure. |
| The export can become stale after Campaign corrections | The file is intentionally external and unmanaged; the GM must generate it again when needed. |
| Very long Campaigns may exceed model context | This case is explicitly out of scope rather than handled by silent truncation. |

## Parking lot for future ideation

### AI-assisted session planning

Design a separate planning experience that can analyze player trajectory,
nearby NPCs and factions, unresolved threads, NPC agendas, active pressures,
and plausible developments. Determine how it enters recap creation and whether
the two paths share interface or data structures. The existing **Prepare Next
Session** Campaign action remains reserved for this work.

### Campaign Seasons

Consider introducing a Season concept above Session for organizing long
Campaigns. Define what creates a Season boundary, whether Seasons are optional,
and how existing Campaigns acquire them before using Seasons in recap browsing.

### Search and filtering within the Scene catalog

Explore navigation aids for large Campaigns, including natural-language search
and filters for Session, NPC, location, faction, or thread. These would enhance
but not replace the complete Session → Scene catalog.

### GM-authored or unrecorded memories

Decide whether the GM may include a remembered event that does not exist in a
recorded Scene Breakdown. This creates tension between flexibility and the
promise that recaps contain established, verifiable events.

### Oversized Campaign context

Design staged retrieval, batching, indexing, or reranking for Campaigns whose
accumulated Scene Breakdowns do not fit in one model context. The initial
feature neither truncates old Sessions nor defines this behavior.

### Presentation customization

Consider optional control over voice, tone, or other presentation choices if a
single concise television-recap prompt proves too restrictive. Numeric Scene
and word limits are not part of the current design.

