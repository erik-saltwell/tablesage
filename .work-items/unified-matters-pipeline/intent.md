# Unified Matters Pipeline: Intent

Rebuild everything after the Ledger as one pipeline that models the Session as threads, which are ongoing pieces of the story, and their facts. The three tiers of Matters become views of that model rather than independent extractions. The pipeline produces three outputs:

- a machine-readable JSON record of previous, current and open Matters
- a Table Recap for reading aloud at the table
- a Session Summary for emailing ahead of time

The goal is higher-quality outputs in which the same information is not restated across categories, because each fact is recorded once by design. Distinct information is still preserved.

This item supersedes [Reduce duplication across Matters within a Session](../reduce-session-matters-duplication/) and its pattern items P1 to P6, which were closed without implementation on 2026-10-29. Their [duplication analysis](../reduce-session-matters-duplication/analysis.md) of Brandonsford Sessions 001 to 004 is this item's evidence.

## Why a Fresh Pipeline

Today each Matters category is produced by its own LLM step. Each step notices the same bargain or threat from its own angle, and every duplication pattern found (P1 to P6) traces back to that. Fixing patterns one at a time with precedence rules or cleanup passes treats the symptom.

Findings from the current code (checked 2026-10-29):

- The forward-looking producers already avoid repeating each other in sequence. Obligations is given the current Goals, Goal Impediments and Opportunities and told not to restate them. In the three open-bargain cases, Obligations did not duplicate anything.
- Developments are generated last and only see New Assets and Revelations. They never see Goals, Obligations or Opportunities, which explains most of the visible repetition.
- Generation order runs almost opposite to reading order: Goals and Present Matters come first and Developments last. So "don't repeat an earlier tier" can't be enforced inside the individual prompts as they're wired today.
- Developments and New Assets describe only the Session just played. Goals, Obligations and Opportunities carry forward, so an open item's forward-looking entry is its only record in later Sessions.

## Framing

The design is a thought experiment that starts fresh from the Ledger. It keeps the existing knowledge of how each Matter is defined and worded, but not the current code after the Ledger.

**Three tiers, each answering one question** (agreed):

- **Previous Matters:** What happened? Developments only; see the New Assets and Revelations decision below.
- **Current Matters:** Where are we? The current position and the immediate danger.
- **Open Matters:** What's ahead? Goals, Goal Impediments, Opportunities, Mysteries and Obligations.

**Duplication principles** (agreed during discussion):

- A situation may appear in both previous and open Matters when it is still unresolved at the end of the Session. Each tier serves a different purpose, so this overlap is legitimate, though repetition still costs the reader something. Completed events appear only in previous Matters.
- "The same thing" means the same fact, not the same story. One bargain can produce several distinct facts, such as the task, the price, the gain and the method, and each should survive.
- Within a tier, no fact is stated twice. Across tiers, a situation may reappear, but only for the part that answers that tier's question.
- Duplication concerns cover every category, not only Developments.

**Categories** (agent recommendations, approved by the user 2026-10-29):

- **New Assets and Revelations** are no longer separate previous-tier categories. What happened, including gains and discoveries, is told in Developments. An asset that is useful later becomes a `could_use` fact shown under "What could help", such as "Warwick's mithril shirt (on loan)". A revelation that matters going forward is recorded as a fact on its thread, marked "learned this Session", for example progress on a Mystery or a new obstacle.
- **Obligations** stay in the model as the `owe` fact kind, because someone waiting on the party is a different motivation from a goal. They keep their own heading, "Promises and debts" (decided 2026-10-29; see Facts).

**Threads are the model's basic unit** (agent recommendation, approved by the user 2026-10-29). A thread holds all its facts, each typed by meaning and tier. Categories and headings are views of threads, so a fact has one home.

## Definitions: Scene, Beat and Thread

Initial definitions, agreed with the user on 2026-10-29. They will be refined by the hand run on Session 004. Sources: today's Scene Log prompt (`packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_scene_log/system.md`) and the Brandonsford Session 004 Scene Log and Ledger.

### Scene

A scene is one group's engagement with one *node*, including its activities, setbacks, retries and aftermath. A node is a place the group goes to and engages, or an event that comes to the group and becomes its focus. A group is the player characters engaged with that node: the whole party, or some of them acting together. Every recorded moment of play belongs to exactly one scene.

- **True to the existing boundaries** (user direction): the definition, scene boundary rules and ordering rules are the Scene Log's, unchanged, so the new scenes match today's. For example, Session 004 keeps its 10 scenes, from Sir Brandon's tomb to the Dwarven mine.
- **Extremely lightweight** (user direction): a scene has only an ID, its location (named by the Scene Log's location rules), the people present, its cue, and its beats in order. The Scene Log's `overview` and `outcome` are dropped. The stopping situation is drawn from the last scene's beats.

### Beat

A beat is one meaningful thing that happened or was learned in a scene, written as one short past-tense sentence. It belongs to exactly one scene and cites the Ledger entries it comes from.

- **Two kinds** (agreed): `event` for an action, interaction, decision, agreement or result, and `learned` for one piece of knowledge, attributed to whoever said it when it rests on their word. These match the Scene Log's Events and Discoveries, one item per beat. The distinction lets a revelation become a fact marked "learned this Session".
- **Granularity:** the Scene Log's. For example, the Warwick's shop scene in Session 004 has about 7 events and 3 discoveries. Routine actions, failed attempts that changed nothing, and repetition are left out.
- **History, not classification:** a beat never labels anything a goal, obligation, threat or other category. It keeps the Scene Log's evidence rules: who agreed to what and on what terms, whose interest something is and whether it is tentative or committed, what remains unknown, and what ended.
- **Importance:** the Scene Log's `high`, `medium` and `low` ratings are kept. They help decide which threads and standalone beats are significant enough for "Last session...".
- **Ledger references:** each beat cites its Ledger entries. This is new compared with the Scene Log, and the grounding check and the Faithfulness dimension depend on it.

### Thread

A thread is one ongoing situation in the story that the players might act on or care about in a later Session. Its identity lasts across Sessions. It is open while any of its facts are still open: something wanted, owed, blocking, usable, unknown or threatening. A thread can open and close within a single Session.

Granularity rules:

1. **One situation, possibly several facts.** The Warwick deal is one thread, even though bringing the metal and returning the shirt are fulfilled separately. Each side is a fact, and the thread closes when none of its facts remain open.
2. **A plan or method is not a thread.** It is a `could_use` fact on the thread it serves. For example, dosing game with faun wine belongs to the dragon hunt.
3. **A sub-thread needs a stated purpose.** A thread is a child of another only when play states that it serves the other. "Find protection against poison" is a child of the dragon hunt because Sir Phidipaldi said it was needed because the dragon is poisonous. The Warwick deal is not a child of the dragon hunt: the shirt was wanted so the party "would not be killed in the Dwarven mine". This follows the Scene Log's rule that a method's stated purpose distinguishes it from an independent goal.
4. **New information joins the thread it bears on.** "The last unidentified map location is probably King Hogboon's" adds to the treasure map thread and does not open a new one.
5. **Not threads:** completed events with no lasting effect, such as camping outside the grave, and colour, such as the drunk goblins' singing. A consequential completed event with no thread is a standalone beat in "Last session...".

A thread has an ID, a short name such as "the Warwick deal", an optional parent, its status at the end of the Session (open, resolved, changed or abandoned), and the beats that touched it this Session. Its facts are added in step 3. **Threads have no category for now** (agreed); the facts carry the kinds.

### Output Decisions

Agent recommendations, approved by the user on 2026-10-29 before pass 3:

- **Brewing Troubles become `threat` facts.** Off-screen dangers that may develop later are open `threat` facts, shown under "Meanwhile". There is no separate Brewing Troubles category.
- **The current tier is "Where you are" and "Immediate danger".** "Where you are" gives the party's position at the end of the Session. "Immediate danger" lists only what is in front of the party now and would demand a response the moment play resumes. Anything that could come later or elsewhere is an open `threat`.
- **The Summary stays organised by category, for now.** This matches today's Summary and keeps the comparison fair. Grouping by thread may be tried later; the user approved this one provisionally.

### Facts

Decided by the user on 2026-10-29, after the [Session 004 hand run](experiments/session-004/README.md#findings-for-the-definitions). Most were agent proposals that the user approved.

- **Facts look ahead only.** The kinds are `want`, `owe`, `blocked_by`, `could_use`, `unknown` and `threat`. The `happened` kind was dropped because it restated beats. "Last session..." is written from each thread's touched beats instead. Knowledge that matters going forward, such as where the dragon's lair is, becomes a forward fact marked "learned this Session".
- **One home thread per fact.** A fact that bears on several threads lives in the one where it is most actionable. Other threads refer to it by fact ID and never restate it.
- **A fact can point at another thread,** for example an obstacle that is itself a thread, such as the goblins' bargain being blocked by Sir Alfred.
- **Bargain tasks are `owe` facts.** A task owed to someone under a bargain, such as "Bring Warwick metal from the Dwarven mine", is `owe`, not `want`. Every `owe` fact appears under "Promises and debts", which keeps Obligations as their own heading. This settles the earlier Obligations heading question.
- **Possibly moot.** A commitment overtaken by events but never released stays open and is flagged *possibly moot*, with the reason. Examples: Dunk's deal with Ingrid after she learned Warwick isn't interested, and Squints' pick after the treasure was sold. A possibly moot fact never appears in open Matters in the Summary or the Table Recap. What happened can still appear in "Last session..." when this Session's beats record it. The flag and fact stay in the JSON. This is a first try.
- **Open-ended promises are facts, but never open Matters.** A promise with no completion condition, mostly a promise never to do something, is still an `owe` fact, because it is something promised. Each `owe` fact has a `definite_end` property: `true` when it has a completion condition and `false` when it does not. Facts with `definite_end: false` never appear in open Matters. They can appear in "Last session..." as part of what happened, and they stay in the JSON. For example, Wayman's promise never to tell King Hogboon where the goblins are. (Amended by the user on 2026-10-29; an earlier version of this decision left such promises out entirely.)
- **Certainty.** Every fact has a `certainty` property: `established`, or `uncertain` with a reason, for things the Ledger leaves unclear. For example, whether Malzazarik and Lady Hilda are still owed payment. (Agent recommendation, approved 2026-10-29.)
- **Money owed to the party is `could_use`.** If the party needs to do nothing to get it, it reads as an asset the party holds. If collecting requires the party to act, it reads as an opportunity, and the fact states the required action. For example, Cedric's promissory note pays out once the caravans flow again.

### IDs

Every scene, beat, thread and fact has an ID (user requirement). The scheme below is the agent's recommendation:

| Item | Scope | Form | Assigned by |
|---|---|---|---|
| Scene | One Session | `scene_<n>` in order | Code, by position, after step 1 returns |
| Beat | One Session | `beat_<n>`, numbered in order across the Session | Code, by position, after step 1 returns |
| Thread | Campaign, permanent | `thread_<n>` | Code. The LLM returns temporary IDs such as `thread_new_1` for new threads, and code replaces them with permanent numbers that are never reused |
| Fact | Campaign, permanent | `fact_<n>` | Code, in the same way as threads |

- **The LLM never makes up a permanent ID.** This follows the existing precedent in `normalize_goal_ids` (`session_pipeline/bundles/campaign_matters.py`): temporary `goal_new_*` IDs become permanent `goal_<n>` IDs, with a high-water mark so concluded IDs are not reused. Code also rejects unknown, duplicate or dangling references.
- **Scene and beat IDs are only unique within a Session,** so a reference from a thread to a beat in another Session includes the Session, for example `004/beat_23`.
- **Facts are permanent** because an open fact, such as a debt, carries forward across Sessions and needs the same identity throughout. Selection and writing are keyed by these IDs.

### Expected Threads for Session 004

The agent's reading of the existing Session 004 Scene Log, not the output of a run. This is the reference to compare the hand run against.

| Thread | Status | What it tests |
|---|---|---|
| Dragon hunt (Eric's bounty) | Earlier, open | Many facts: the sword works against evil, the lair's location, the faun wine plan |
| ↳ Protection against poison | New, open, child | A child linked by stated purpose |
| Treasure map | Earlier, open | Discoveries join it: Dragon's lair, the Dwarven mine, possibly Hogboon's location |
| Warwick deal | New, open | One thread with two sides as facts |
| The goblins' bargain | Earlier, changed | The same counterpart stays one thread; it gains a new promise never to tell Hogboon where the goblins are |
| Robes for Brother Dirk | New, open | A plain promise |
| Recruiting Malzazarik and Lady Hilda | New; recruitment done, payment still owed | Stays open only because something is owed |
| Vivian's letter to Grimny | New, resolved | Opened and closed in the same Session, so it appears only in "Last session..." |
| Who killed Grimny, and where is the hoard | New, open | A question thread: Bral, and the Dragon's Lair |
| Ingrid and Warwick (Dunk's 002 deal) | Earlier; probably abandoned | Forces a decision on an earlier thread |
| Sir Alfred | Borderline | Incapacitated but not destroyed: a lasting threat or a standalone beat? A test of judgement |

### Experiments

- [Pass 3: prompts for steps 4 to 8](experiments/session-004/pass-3/README.md) (2026-10-29). New Summaries and Table Recaps for Sessions 003 and 004. Today's restatements are gone, and the present danger is told once. Selection needed four threshold revisions and is the main open problem; the agent's mechanism for telling the present danger once (step 4 marks the `threat` facts it covers) needs approval.
- [Pass 2: prompts for steps 1 to 3 on Session 004](experiments/session-004/pass-2/README.md) (2026-10-29). Steps 1 and 2 met the quality bar, with stable results across runs. Step 3 as designed, with parallel per-thread calls, did not meet one home per fact: it often placed the same fact on two threads. A single-call variant did better but still repeated shared details. A third variant, a homes step that names one home thread per shared subject before the parallel calls, met the whole bar in all three of its final runs. Facts in every variant sometimes overreach their beats. The user chose the homes step on 2026-10-29; see step 2 in Proposed Pipeline. Folded into step 2, it met the bar on both Session 004 chains. On Session 003 the prompts transferred well; three gaps found there were fixed, and the final prompts met the bar on both Sessions. Overreaching facts and speculative questions remain.
- [Hand run: Session 004, steps 1 to 3](experiments/session-004/README.md) (2026-10-29, pass 1). The agent applied the definitions by hand, without prompts. All 11 expected threads emerged, plus Missing shipments, and the Warwick cluster resolved into one thread with distinct facts. Its findings were decided the same day; see Facts.

## Proposed Pipeline

The user chose this design on 2026-10-29. A four-step alternative was considered and set aside: decide what's true, what to keep, where it goes, and how to phrase it.

| # | Step | Kind | Output and purpose |
|---|---|---|---|
| 0 | Inputs | – | Ledger, prior Campaign State (open threads with IDs, last stopping situation), roster, Glossary |
| 1 | Scenes and beats | LLM, 1 call over the whole Ledger | Ordered scenes, each with its location, the people present, a scene cue and its beats. Beats are `event` or `learned` items with Ledger references, and every later step cites them. Code assigns scene and beat IDs. See Definitions, and Scenes, Threads and Cues |
| 2 | Thread reconciliation | LLM, 1 call, strongest model | The state of every prior thread (open, resolved, changed or abandoned) and the beats that touched it, plus new threads and parent links. Decides thread identity once, and forces a decision on every prior thread, which addresses staleness. Also names one home thread for each subject that several threads bear on, so the parallel step 3 calls record it once (decided 2026-10-29 after pass 2; tested as a separate call, which may stay separate if folding it in hurts step 2) |
| 3 | Thread facts | LLM, 1 call per touched or open thread, in parallel | Typed single forward-looking facts (`want`, `owe`, `blocked_by`, `could_use`, `unknown`, `threat`), each with a home thread, evidence and ratings for importance and actionability. One call per thread gives each fact one home. Empty kinds are normal |
| 4 | Stopping situation | LLM, 1 call | Current position and immediate dangers, linked to threads, focused on the end of the Ledger |
| 5 | Selection | Deterministic | What each output includes, using rules plus rating thresholds and limits from `settings.yaml`. Open Matters exclude facts flagged *possibly moot* and `owe` facts with `definite_end: false`. JSON gets everything |
| 6 | Summary writing | LLM, 1 call | Read-aloud text for each selected item, keyed by item ID. One writer sees the whole layout, so each bullet states only its own fact. Also picks the Session cue by scene ID |
| 7 | Render JSON and Summary | Deterministic | The updated Campaign State plus this Session's view, and `summary.md` from a template. Code checks the chosen scene ID and copies that scene's cue word for word into the Summary's title line, and records it in the JSON |
| 8 | Table Recap | LLM, 1 call | Spoken prose built from the selected structured view, not from parsed Summary Markdown. Organised by thread, short, in second person, ending with the stopping situation. Uses its own, tighter selection |
| 9 | Grounding check | LLM, cheap model, optional | Reports bullets not supported by their cited beats. For review, not a hard gate |

Deterministic checks between steps: references are valid, every prior thread is accounted for, there is one text per item, no thread has two facts of the same kind and evidence, and IDs are assigned in code.

### Scenes, Threads and Cues

Agreed with the user on 2026-10-29.

Scenes and threads organise the same beats along different axes, and neither contains the other:

- **A beat** is one thing that happened.
- **A scene** answers *when and where*. Every beat belongs to exactly one scene, and scenes are ordered.
- **A thread** answers *which story*. It points at beats, which may come from several scenes and several Sessions. A beat can belong to more than one thread, or to none.

Step 1 cuts the Ledger by time into scenes holding beats. Step 2 ties beats together by story into threads. For example, the Session 004 Warwick deal is one thread whose beats sit in two scenes: at Warwick's house and at the mine.

**Cues belong to scenes, not threads.** A cue is a short phrase, about ten words or fewer, naming the most vivid thing the players will remember a scene by: a sight, an odd remark, a distinctive item. It deliberately picks what was most memorable, not what mattered most. The real Brandonsford Session cues show why: "Drop Dead Ned's killer wasp in a jar necklace" (001), ""Ow, why did you do that?" - Squints" (002), "The goblins' peeled white speaking stick" (003), ""My loins will forever burn with the heat of the forge" - Vivian" (004). These are moments, mostly unconnected to any plot thread. Thread cues were considered and rejected for three reasons: they would favour importance over memorability, threads span Sessions so their cue would repeat or need reworking, and many memorable moments belong to no thread.

**Carry over the Scene Log's cue rules.** Today's Scene Log already produces a `scene_cue` per scene and picks the most memorable as the `session_cue`, which becomes the Summary's title line. Its cue guidance in `generate_scene_log/system.md` carries over: about ten words, vivid over important, quotes cut from the Ledger's own wording and credited to the character. The new pipeline moves the Session cue choice into step 6 so it happens while the Summary is built, as the user wants. Choosing needs only the cue texts. Picking by scene ID, with code copying the cue, keeps the "copy the cue exactly" guarantee.

**Keep scenes lean** (agreed): an ID, location, the people present, cue and beats. The Scene Log's per-scene `overview` and `outcome` are left out, because Developments now come from threads and a per-scene summary would be one more place to restate things.

**Scenes also give:** the order for "Last session...", context about where and with whom for step 2, and a natural unit for splitting step 1 if that is ever needed.

**One call to start** (agent recommendation, accepted): step 1 runs as a single call over the whole Ledger, as the Scene Log does today. Building each scene from its own slice of the Ledger was considered. It is deferred, because beats often depend on earlier scenes, cues are chosen partly to tell scenes apart, and scene boundaries would become one more thing that could go wrong. Switch to per-scene calls only if long Sessions show a quality or length problem, and then give each call the full list of scenes as context.

### How the Output Views Use Threads

- **"Last session...":** one bullet per significant thread touched, written from that thread's touched beats and ordered by the scene where its first beat happened, plus important standalone beats.
- **Current tier:** from step 4.
- **Open headings:** each forward-looking fact goes under its heading: `want` → goals, `owe` → promises and debts, `blocked_by` → standing in your way, `could_use` → what could help, `unknown` → still unanswered, `threat` → meanwhile.

**Fact meaning, not headings** (agent recommendation, approved by the user 2026-10-29): step 3 records what a fact means (for example, "a task, owed to Warwick, in exchange for the shirt"), not which heading it goes under. This keeps placement mechanical rather than another judgment call by an LLM.

**Expected effect on the analysed patterns:**

- **Bargains (P1, P2, P5, P6):** each bargain is one thread, and each side of the deal is one fact.
- **P3:** a revelation that blocks progress becomes one `blocked_by` fact, marked as learned this Session.
- **P4:** the threat is one thread. The current tier owns "it's here now", and an open threat survives only if it is distinct.

For example, the Session 004 Warwick deal would read: Last session "The party promised Warwick metal from the Dwarven mine in return for the loan of his mithril shirt"; debts "Bring Warwick metal from the Dwarven mine" and "Return Warwick's mithril shirt"; obstacle "A cave-in seals the mine"; what could help "Warwick's mithril shirt (on loan)". The digging Opportunity disappears because it restated the obstacle.

## Rollout: Side by Side, Then Cut Over

Settled by the user on 2026-10-29. The new pipeline produces new versions of the existing artifacts, such as the Table Recap and the Session Summary, alongside the current ones. Nothing existing is removed or changed until the user is happy with the quality of the new outputs.

The reason is comparison. The existing artifacts are good in many ways, and apart from the duplication they set the quality bar. Seeing the old and new versions of the same Session side by side is how we make sure the new work keeps everything that was good about them.

The very last step is the cutover, when the new outputs replace the old ones under the existing artifacts' names. See Cutover for how.

**Hidden until cutover** (user decision, 2026-10-29): the new artifacts do not appear in the app in any way before cutover. They show up in the app only at cutover, when they replace the old ones.

**Regenerated from Ledgers** (user decision, 2026-10-29): every Session is regenerated from its Ledger by the new pipeline. Sessions run in order, because each Session reads the Campaign State left by the one before it.

**Naming while side by side** (agent decision, delegated by the user, 2026-10-29): every new output goes in a `unified/` subfolder of the Session folder, with nothing new at the Session folder's top level. The final outputs use the same base names as the artifacts they will replace, so a comparison is the same filename in two folders:

| New file | Compare with | Contents |
|---|---|---|
| `unified/summary.md` | `summary.md` | Session Summary |
| `unified/table_recap.md` | `table_recap.md` | Table Recap |
| `unified/matters.json` | `post_session_matters.json` | Previous, current and open Matters for this Session, plus the Campaign State the next Session reads |
| `unified/scenes.json`, `unified/threads.json`, `unified/thread_facts.json`, `unified/stopping_situation.json` | – | Intermediate outputs of pipeline steps 1 to 4, kept for inspection |

Checked 2026-10-29: nothing in the app should pick up or delete a `unified/` subfolder. Orphan cleanup for Sessions only removes unknown folders directly under the Campaign folder (`entities/sessions.py`), and the Matters ID counter only scans files one level below it (`session_pipeline/campaign_matters.py`). Clean Session deletes only registered artifacts, so `unified/` survives it; the next run overwrites it. Campaign archives copy everything (`campaign_archive.py`), so exported or backed-up Campaigns include the `unified/` files. That is harmless, since no screen shows them.

### Running Before Cutover

Agent recommendation, accepted by the user on 2026-10-29. Add a hidden subcommand to the existing `tablesage` command:

```
tablesage generate-unified-matters --campaign Brandonsford             # every Session, 001 onwards
tablesage generate-unified-matters --campaign Brandonsford --session 4 # one Session, from 003's unified state
```

- **Follows an existing pattern:** `tablesage regenerate-table-recap` and `regenerate-session-summary` (`apps/tablesage-tui/src/tablesage_tui/cli.py`) already run in a workspace without opening the app. They check the database revision, load `.tablesage/settings.yaml` with `ensure_settings`, and build an `Application` with those settings. The new command copies that.
- **Hidden:** left out of `--help`, never visible in the TUI, and removed at cutover.
- **Ordering:** the default regenerates every Session in order, because each reads the Campaign State the previous Session wrote to `unified/matters.json`. `--session N` reruns one Session from the previous Session's saved state, for quicker prompt iteration. It refuses to run if that state is missing.
- **No freshness tracking:** every run regenerates what it covers. Dependency tracking waits for cutover, which keeps the experiment cheap.
- **Debugging:** raw LLM responses are saved under `unified/.generation-records/`, as the current steps do. A run stops at the first failure and reports the Session and step.
- **Settings:** tunable values go in a new `AppSettings` section and the packaged `settings.yaml`, following the project's settings rule. If the Settings screen lists sections automatically, keep the new section off it until cutover, so nothing shows in the app early.
- **Code:** a new module in `tablesage-application` with its own prompts. Before cutover, nothing existing changes apart from adding the command and the settings section.

### Cutover

Agent recommendation, accepted by the user on 2026-10-29. It refines the original idea of renaming the new files into place: because every Session is regenerated from its Ledger anyway, cutover switches the code and then regenerates, with no file moves.

1. **Register the new artifacts** in `ArtifactName` (`artifact_registry.py`) and the dependency graph (`session_pipeline/artifact_graph.py`): Ledger → scenes → threads → thread facts → stopping situation → Matters → Summary and Table Recap. Include the previous Session's Matters as an input, as the current Matters steps do (`application.py`, around the `prior_folder` references), so a change in one Session marks later Sessions out of date. Fingerprint the prompts and the new settings, as the current graph does.
2. **Feed the Table Recap from the structured Matters,** not from the Summary's Markdown.
3. **Show only the three outputs in the app.** Keep intermediate files internal, as today's per-category Matters files are.
4. **Retire the old producers:** Post-Session Matters, Present Matters, the per-category Matters artifacts with their prompts and ID counter (`.matter-ids.sqlite3`), and the current Summary and Table Recap producers.
5. **Archive, then regenerate:** archive the old outputs using the existing content-hash `legacy/` convention, run Regenerate All Outputs for each Campaign, then delete the `unified/` folders and the hidden command. The final name of `matters.json` is decided at this point.
6. **Update contracts and documentation:** write a new specification replacing the Matters Port, Post-Session Matters, Deterministic Session Summary and Spoken Table Recap contracts, and update the list in `.agent_context.md`. Update the public `docs/`, since New Assets and Revelations disappear as headings, and recapture documentation screenshots.

## Constraints

- Keep each Matter's existing definitions and read-aloud wording rules. They move into the fact kinds in step 3 and the writing in step 6.
- Tunable knobs for calls into `tablesage-tools` come from the TUI's `settings.yaml` (see `.agent_context.md`).
- Verify by building, running, and comparing outputs on real Sessions such as Brandonsford. Do not add unit tests (see the [engineering workflow](../workflow.md)).
- Before changing artifact schemas, prompts, routing, persistence or invalidation, read the relevant specifications listed in `.agent_context.md`. This work will supersede parts of the Matters Port, Post-Session Matters, Deterministic Session Summary and Spoken Table Recap contracts.

## Acceptance Conditions

- All three outputs are produced from the Ledger and prior Campaign State through the unified pipeline.
- Before cutover, the new outputs are compared side by side with the existing artifacts for the same Sessions, and they keep the existing artifacts' strengths.
- Cutover happens only once the user is satisfied with the quality of the new outputs.
- On the analysed Brandonsford Sessions, the restatements recorded in the analysis no longer appear, and the distinct facts they sat beside still do.
- Each open thread from a prior Session is either carried forward or explicitly resolved, changed or abandoned.

## Unresolved Questions

- **GM review.** Whether thread reconciliation should be reviewable by the GM, since its mistakes spread to every output.
- **The recruitment thread's framing.** Step 2 consistently names it "Cedric's promissory note" rather than "Recruiting Malzazarik and Lady Hilda", with the recruits' payment as an uncertain debt on it. That's defensible, but it differs from the expected-threads table.
- **Cost and latency** of a single writing call over the whole Summary, and of step 3 on long Sessions.
- **The Scene Log at cutover.** Step 1 takes over the Scene Log's role for this pipeline, including the Session cue. The Scene Log also feeds other parts of the app, such as the processing gate (`session_pipeline/processing.py`, `processing_steps.py`) and campaign scene logs. Whether it is retired or kept for those uses needs a decision.
- **Other readers of Matters.** Each part of the app that reads the current Matters, including `processing_steps.py`, `session_summary.py` and possibly the campaign preparation tools, must be pointed at the new Matters or retired. This needs checking before cutover.

## Quality Rubric

Revised 2026-10-29 at the user's direction for this item's broader scope. It replaces the rubric carried over from the superseded parent item, [approved there the same day](../reduce-session-matters-duplication/intent.md#quality-rubric). The user agreed to drop that rubric's *Grounded in real Sessions* and *Narrow, pattern-specific handling* dimensions, which were about the design of per-pattern rules. *Pattern resolution*, *Information preservation* and *Best representation* are kept, reworded for the thread model. The other dimensions (Faithfulness, Continuity, Selection and Fit for each output) were proposed by the agent. The user approved the full rubric on 2026-10-29. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the pipeline's outputs for real Sessions: the Matters JSON, the Session Summary and the Table Recap.

- **Faithfulness:** Every fact in the outputs is supported by the Ledger or by prior Campaign State. Nothing is invented, and names, amounts, conditions, sources and uncertainty are kept. This is about the content of the outputs, not about the evidence behind the design.
- **Continuity:** Threads keep the same identity across Sessions. A thread from a prior Session is carried forward, or explicitly resolved, changed or abandoned, so nothing stale lingers and nothing open quietly disappears. Distinct threads are not merged, and one thread is not split in two. This is separate from Faithfulness: every fact can be true while the thread structure is wrong.
- **No restatement:** A reader does not meet the same fact twice within a tier. Where a situation appears in more than one tier, each appearance gives only that tier's angle: what happened, where things stand, or what's ahead. This holds consistently across Sessions.
- **Information preservation:** No useful information is lost. Each distinct fact survives, such as each side of a bargain, a price owed, an obstacle, or whether something is on loan, even when it shares a story with other facts. Similar subject matter alone is not treated as duplication. This pulls against No restatement: an aggressive approach does well there and badly here.
- **Selection:** Each output includes what matters most for its purpose and leaves out trivia. The Table Recap keeps less than the Summary, and the JSON keeps everything. This pulls against Information preservation, which asks that useful facts survive somewhere, not that every fact appears in every output.
- **Best representation:** Each fact appears in the tier and under the heading where it helps the reader most: what happened reads as an event, what the party must do as a goal or debt, what it can use as a resource, and how it might proceed as an option. This is separate from the other dimensions: an approach can avoid repeats and keep every fact, yet put a fact in the weaker place.
- **Fit for each output:** Wording and form suit how each output is used. The Table Recap is brief and natural when spoken, tells each thread once, and ends where play resumes. The Summary is easy to scan ahead of a Session. Each bullet stands on its own in plain words. This is separate from Best representation: the right fact can be in the right place and still be clumsy, too long, or awkward to read aloud.

Simplicity is deliberately not a dimension.

No evaluation has been performed against this rubric.

## Implemented Review Refinements (2026-10-31)

The user approved and requested implementation of review changes #1–#3 in the unified experiment. [Pass 7](experiments/session-004/pass-7/README.md) is now the implementation revision for those changes; existing pass 6 outputs remain evidence from the prior contract. Supported implicit opportunities use `action_supported` without requiring a spoken proposal, while negotiated offers still require established terms. Distinct resources receive independent facts; a shared-resource pointer is suppressed only against an eligible selected home fact with matching resource identity and complete content. Lasting impediments require explicit scope evidence and a live shown target, while the stopping-situation writer can claim the same immediate confrontation recorded as an obstacle. See [Implementation Progress](progress.md) for the exact scope, conservative deduplication tradeoff and checks.

This overrides earlier statements that no implementation was authorized only for these three approved refinements. It does not authorize production cutover. The intentional table-revelation preference is retained without adding a character-only knowledge rule. The Last session cutoff remains unchanged; its [low-impact/high-lasting comparison](../allow-low-impact-developments-high-lasting-consequences/intent.md) is deferred. No new Session generation or output-quality evaluation has been performed.

## Approved Session 001–002 Review Refinements

The user approved recommendations 1–9 in [EX-070–EX-078](../../learnings/README.md#summary-headings), with three clarifications: the unaccepted duel has no explicit withdrawal and need not survive its scene; assets are not open matters; an immediate intention appears only if one is established. The agent's proposed asset grouping inside What could help is explicitly superseded. Held assets remain campaign memory and may be historical gains, but are excluded from open headings and forward-looking Recap inputs. Preserve the source and uncertainty of every claim.

[Pass 8](experiments/session-004/pass-8/README.md) implements the approved lifecycle/significance guidance, adventure-first ordering, canonical publication reconciliation for equivalent offers/plans, exclusion of tautological/generic openings, classification continuity, optional current intention and simpler historical headlines. This supersedes pass 7 as the current implementation revision; old outputs remain historical evidence. The existing qualitative rubric is unchanged. Direct mechanics were verified; no fresh model outputs or quality judgments exist for pass 8. Production cutover and the low-impact/high-lasting experiment are outside this change.

## Approved Historical Encounter Coverage (2026-11-01)

EX-079 exposes loss of an encounter when its facts are distributed among threads and its remaining purchase thread is incidental. The user approved a general remedy: historical assessment receives full encounter context and may publish one concise, otherwise-unrepresented noteworthy interaction independently of open-goal importance or lasting effects. This explicitly expands the historical definition; do not inflate ratings or pretend the global historical policy is unchanged. It does not require a bullet per scene/character or allow routine colour/logistics by default. Same-event representation is distinct from simply sharing a location, person or information.

Implemented in pass 9's existing step 2c call with scene candidates, evidence-bearing focus beats and explicit representation links, followed by deterministic validation/selection. No additional model call was added. The old thread/event conjunction remains. Open matters and their filters are inherited from pass 8. Low-stakes commitments and the separate low-impact/high-lasting comparison remain deferred. The user requested fresh Sessions 001–002 and review copies after this update.

## Approved Pass 12 Refinements (2026-11-01)

The user approved the seven general proposals following the pass 11 review with “implement then run pass 12”. Distinguish supported desired ends from proposed methods; classify incidental goals by what achieving their particular outcome changes, retaining adventure goals. Obstacles must causally constrain the actual outcome and cannot survive solely on a hidden pursuit. Paid jobs state their success condition and reward, with techniques separate.

“Still unanswered” now has two eligibility paths: meaningful revelation questions and grounded, unresolved investigative questions defining a live adventure objective. The latter may pass despite low independent narrative payoff or depth, but requires a real investigative objective, open-ended question, adequate grounding/potential and a validated link to a shown adventure goal. Routine tactical/logistical unknowns are excluded. This intentionally broadens the old Mystery definition; it does not publish every unknown on an adventure thread. Reassess questions when evidence changes rather than freezing a prior low rating.

Apply relevance to individual details in all headings, while preserving independently noteworthy historical encounters. Context can make an opportunity's benefit clear without an added mechanism explanation. Prefer a concise single sentence, permitting a second for an essential condition, attribution or uncertainty.

Goal order is deterministic: primary adventure goals, other adventure goals, then meaningful side goals, followed by importance and stable ties; actionability cannot outrank narrative priority. History order is deterministic from the actual narrated event's cited Ledger position, not the first mention of its thread. Historical assessment supplies validated anchors and focused evidence for every candidate. No extra model call is required. Production cutover and the deferred low-stake/low-impact-high-lasting experiments remain outside this approval.


## Approved Pass 12 Review Refinements (SRC-60, 2026-11-01)

The one-at-a-time review resolves the distinctions recorded in learnings: danger must be established rather than inferred from generic risk or lost prospective benefits, without requiring quest acceptance; the adventure driving current party choices comes first; opportunities provide an advantage rather than merely attaining their own goal, merge complementary supported plan components, and use conditional action/advantage wording. Full contract evidence remains in state while displayed opportunity wording may omit fee/rebate precision. First-mention recognition cues are optional, including for familiar people. Eligible open matters may repeat unchanged across Sessions. Meaningful historical interactions can retain brief contextual detail; current situation detail must orient the next moment. Preserve grounded underlying mystery candidates from unexplained changes and contradictions before rating them.

Specific reviewed allowances and severity do not become named prompt rules: targetless obstacle omission and the ordinary sons-outcome mystery omission are allowed; a brief mule-offer history detail is optional; penance remains acceptable for now; the map-related goal/question wording and missing challenge history are minor. Separate low-stakes commitment and low-impact/high-lasting investigations remain deferred. The user requested learning/prompt implementation after discussion; [pass 13](experiments/session-004/pass-13/README.md) implements the generic guidance without fresh generation or schema/threshold changes.
