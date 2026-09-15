<overview>
Generate a review-ready set of closed-ended coverage questions from a TableSage Ledger JSON document.

The questions will be used to judge whether another ledger preserves the important fiction recorded by the source ledger. The output is an intermediate artifact for a human reviewer, not the final evaluation file.
</overview>

<source_contract>
- The sole source is one JSON object representing a TableSage ledger.
- Use only information stated in that ledger. Do not use outside knowledge.
- Use structural fields to interpret each fact; do not treat the JSON as undifferentiated prose.
- Administrative metadata—including `version`, `session_id`, `session_name`, attendees, player names, and role assignments—is context only and must not generate questions.
</source_contract>

<ledger_structure>
Analyze the source in this order:

1. `preamble.recap.events`
   - Consider every important fact in the recap for required coverage.
   - Split compound recap entries into meaningful coverage units using the rules below.

2. `preamble.character_introductions`
   - Consider every important introduction fact for required coverage, with no per-character quota.
   - Identity, role or archetype, consequential capabilities, limitations, equipment, relationships, and distinctive traits may be important.
   - Generic appearance and interchangeable flavor are not important merely because they are present.

3. `utterances`
   - Read entries in order and interpret their `type` and semantic fields.
   - Adjacent entries may be parts of one event. Understand the complete event before extracting atomic facts; do not generate a quota of questions per entry.
   - For `question` entries, treat the resolution as authoritative when one is present.
   - For `correction` entries, use the corrected canon and suppress superseded facts.
   - Treat the entry type as an evidence boundary. Narration, action, correction, and resolved-question entries may support direct questions about what happened. A speech entry establishes that its named entity communicated something; it does not independently establish the statement's content as objective world truth.
   - Questions derived from speech must use a communication verb such as "tell", "say", "claim", "report", "warn", "offer", "promise", or "ask", and must name the speaker.
   - Name the recipient or audience when their identity materially distinguishes the conversation or helps interpret the fact. Use adjacent entries to recover that conversational context. Do not add a listener merely because one can be inferred when the listener does not improve the question.
   - Prefer "Did Farmer Gill tell Dunk that Sir Brandon killed the dragon?" when identifying Dunk distinguishes that conversation. "Did Farmer Gill say that Sir Brandon killed the dragon?" is sufficient when only the source of the claim matters.
   - Preserve nested attribution. If Eric reports what George said, ask whether Eric reported George's claim; do not phrase the question as though George spoke directly in the ledger.
   - Remove attribution only when an authoritative narration, action, correction, or resolution independently establishes the same fact.
   - For beliefs, rumors, plans, and uncertain claims, preserve both attribution and epistemic status rather than converting their content into objective truth.
   - Distinguish plans, attempts, successes, failures, and unresolved actions precisely.
</ledger_structure>

<selection_policy>
First extract and normalize candidate coverage units across the entire ledger. Deduplicate them before writing questions.

A fact belongs in `required_candidates` when it is narratively meaningful in the session. This includes meaningful fictional actions, events, discoveries, decisions, outcomes, state changes, material causes, and facts useful for interpreting later events.

Apply the rule of reincorporation: require a fact when the ledger provides a reasonable basis to believe it might return later or help interpret future events. Do not promote a detail merely because it could hypothetically return; when future relevance is uncertain, judge it by its importance in the current session.

Place a fact in `optional_candidates` only when a reasonable reviewer might still promote it, but it is primarily distinctive color, incidental method, nonessential explanation, or reasonably inferable from a required fact. Optional candidates are a short judgment-call queue, not a dump of all rejected facts, and may be empty.

Prefer concrete fictional assertions over incidental characterization. Preserve identity, action, possession, relationship, and state. Remove appearance, attitude, subjective evaluation, and explanatory motivation unless the detail is itself narratively meaningful or reasonably likely to matter later.

Exclude:
- administrative metadata;
- trivial movements, gestures, and conversational transitions;
- incidental appearance, generic atmosphere, and interchangeable description that neither distinguishes an important entity nor aids future interpretation;
- out-of-character table talk;
- rules discussion, dice rolls, modifiers, damage calculations, and mechanical procedure.

Also omit an unsuccessful check, failed attempt, or negative observation when it changes nothing, produces no useful discovery, influences no later decision, and creates no potential for reincorporation. Include it when the failure itself has a consequence or becomes meaningful fiction.

Omit a fact when it merely restates an obvious implication of another retained fact. Also omit vague self-assessments, inactive motivations, and minor transactions or actions that have no apparent narrative effect or reincorporation value.

Expressions and reactions can be important when they establish acceptance, disbelief, hostility, trust, fear, or another stance that changes how surrounding dialogue or subsequent action should be interpreted.

Include a mechanically expressed fact only when it creates durable game state or explains a consequential fictional outcome. Prefer the fictional result over the procedure that produced it.

If two entries repeat a fact, write one question using the most authoritative and informative formulation. Corrections and explicit resolutions control conflicting earlier material. If a genuine conflict remains unresolved, do not generate a required question for the disputed fact; add a concise note to `review_notes` instead.
</selection_policy>

<question_rules>
- Every question must be closed-ended and answerable with either "yes" or "no".
- The answer to every question must be "yes" based solely on the source ledger.
- Each question must test one meaningful coverage unit.
- Split a question when its parts represent separate events, claims, consequences, or independently useful facts that a reviewer might reasonably keep or discard separately.
- Closely related descriptors of one entity may remain together when a reviewer would naturally keep or discard them as one coverage unit.
- A shared source entry, subject, scene, or sentence does not by itself make multiple claims one coverage unit.
- Conjunctions may form one identity, relationship, group action, or tightly coupled description. Do not use them to bundle separate offers, decisions, causes, outcomes, or narratively distinct actions.
- For example, split "Did an innkeeper offer rooms and pour a free drink?" because those events have separate narrative value. "Do Dagonites have extremely pale skin and unusual eyes?" may remain together as one compact physical description. "Did A, B, and C enter the tavern together?" may remain together because it tests one group action.
- Preserve attribution, uncertainty, negation, quantities, relationships, and temporal status when relevant.
- Make every question understandable in isolation and robust to reordering or removal of neighboring questions.
- Name the relevant entities and include concise scene context when it helps identify the person, object, conversation, or event—for example, "the thief in the Clumsy Fox" rather than an unanchored "the thief".
- Prefer natural, direct wording. Include only the context and qualification necessary to preserve the fact accurately; do not make questions technically exhaustive at the expense of clarity.
- When simplifying, do not strengthen suspicion into fact, investigation into accusation, possibility into certainty, or a plan into its intended outcome. Preserve exactly what the source knew, believed, offered, and intended at that moment.
- Do not refer to "the ledger", "the text", field names, entry numbers, or nearby questions.
- Do not generate redundant paraphrases of the same fact.
- Do not pad the lists or impose a minimum, target, or maximum question count.
- Before returning the JSON, audit every candidate by asking whether its parts have different narrative or reincorporation value. If a reviewer might reasonably retain one part but remove another, split the question or retain only the important part.
- For every candidate derived from speech, audit all of the following:
  1. Does the question name the speaker?
  2. Does it describe the content as something communicated rather than as objective world truth?
  3. If the statement is hearsay, does it preserve the relevant attribution chain?
  4. Is the recipient named when that identity materially distinguishes the conversation or helps interpret the fact?
  Rewrite any candidate that fails this audit.
- Finally, audit every paraphrase for epistemic drift. Rewrite any question that turns an unresolved belief into truth, an attempt into success, an investigation into an accusation, or an intended outcome into an accomplished one.
</question_rules>

<review_notes>
Use `review_notes` only for unresolved factual conflicts, genuine ambiguities, and unusually close required-versus-optional judgments. Each note must be a short standalone string. Do not justify routine candidate choices and do not attach metadata to every question.
</review_notes>

<output_format>
Return only valid JSON with exactly these four keys in this order:

{
  "required_candidates": [],
  "optional_candidates": [],
  "review_notes": [],
  "questions": []
}

- All four values must be lists of strings.
- Order both candidate lists by source order: recap first, character introductions next, then session chronology.
- `questions` must be the final key and must always be an empty list. It is a ready-made destination for the human reviewer to copy retained candidate strings into.
- Do not include markdown, comments, explanations, or additional keys.
</output_format>
