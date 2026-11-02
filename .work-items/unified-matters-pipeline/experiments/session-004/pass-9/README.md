# Pass 9: Encounter-Level Historical Coverage

Implements the general remedy approved after [EX-079](../../../../../learnings/examples/last-session.md): a meaningful encounter should not disappear from Session history merely because its information was divided among threads or its open desire is incidental. The exact omission and user approval were preserved before behavior changes. Pass 8, earlier review copies and production artifacts remain intact.

## Scope and Policy

Step 2c still makes one historical-assessment call. Its input now includes full scenes/people/beat IDs, touched threads, standalone events and each scene as a possible encounter. Scene presence alone never requires a historical bullet. Existing thread/standalone selection still requires medium/high narrative impact and lasting consequence. The new encounter channel explicitly assesses independent historical value: a meaningful meeting, hospitality or information exchange may merit coverage despite low lasting consequence and no open matter. It does not falsify impact/lasting ratings to satisfy the old threshold.

Each scene candidate has encounter_basis, encounter_value, focus_beats and represented_by. Medium/high encounter_value with supported focus beats qualifies unless a selected thread/standalone historical candidate already tells the same central event. Shared people/location or merely scattered pieces of information do not establish duplication. Routine shopping, logistics, colour, length or character appearance alone do not qualify. There is no scene/character quota, no invented alliance and no special rule naming Dunk, Gill or a mule.

Code validates exact candidate accounting/order, scene-local focus IDs and existing representative IDs. An unselected representative cannot suppress an encounter. Semantic historical value and same-event judgments remain LLM assessments, documented with their evidence; ID validation cannot prove those judgments correct. Source scenes, threads and facts remain intact.

The Summary writer receives only the selected encounter focus beats as a separate encounter item. History remains chronologically ordered by supporting beats. Rendering keeps its scene ID in previous items, and the Recap receives it as historical material. Open matters, asset exclusion, goal priority, opportunity reconciliation and commitment filters are inherited from pass 8 without policy changes. Low stake commitments are still eligible under the existing rules; their [investigation](../../../../filter-low-stakes-commitments/) remains deferred.

This is an approved addition to historical coverage, **not** the separately deferred low-impact/high-lasting A/B investigation. The original thread/event cutoff is retained, but the overall historical policy has expanded. Future comparisons must freeze the same baseline and encounter policy for both conditions rather than treating pass 8 and pass 9 as a controlled cutoff comparison.

## Generation

The requested fresh chained Sessions 001–002 are complete. Session 002 received Session 001's fresh seed including full classification metadata. Initial Session 001 seed is empty. Inputs, stages and implementation hashes are saved in generation-inputs.json and generation-journal.json. No earlier pass seed or model output is silently adapted as a new result.

Use run9.py with the same step1, step2, step2c, step3, check, chain and seed commands as pass 8. For each Session, generate steps 1–3, then chain (defaults to --from 3 for opportunity reconciliation through Recap). After s001, run seed s001 002 before generating s002. A new step2c run is mandatory for the scene candidates/new fields; old changes.json does not meet this contract. Resume behavior is otherwise inherited from pass 8. Preserve raw evidence before any targeted retries.

Review destination: deployment/unified-review/14-PASS9/. Completed generation/copy results are recorded below.

## Verification Before Generation

[verification.json](verification.json) records 64 passing direct behavior checks using explicit saved-fact fixtures and stubbed writing boundaries, not fresh LLM outputs. Checks cover existing selection/reconciliation/continuity/rendering mechanics, all 16 thread/event rating combinations, new encounter inclusion/exclusion, eligible-versus-hidden representation, invalid scene focus/references, propagation to Summary/Recap/historical JSON, unchanged open-matter contracts and the deferred low-stakes work-item status. Python syntax, schema parsing and CLI loading passed. No unit-test files/tooling were added.

Quality dimensions remain the existing qualitative rubric: Faithfulness, Continuity, No restatement, Information preservation, Selection, Best representation and Fit for each output. Actual encounter-value calibration and semantic duplicate suppression await new output review; no quality scores or user verdicts are claimed by direct verification.

## Completed Generation and Review Copies

Fresh Sessions 001–002 completed in order and are copied to [14-PASS9](../../../../../deployment/unified-review/14-PASS9/0-START-HERE.md). Summary, Recap, kept/dropped and JSON copies match the source bytes; supporting beats/threads/facts are rendered in Markdown for phone review. Root unified-review guide points to this pass; earlier copies remain unchanged.

Session 001: 5 scenes, 37 beats, 10 threads, 23 facts; 8 historical items (one encounter) and 11 open facts; Summary 458 words, Recap 313. Session 002: 13 scenes, 86 beats, 16 threads, 51 facts; 10 historical items (two encounters) and 20 open facts; Summary 665 words, Recap 449. All Recap bullets meet the nominal 35-word limit.

Session 001 now tells Dunk's encounter with Gill: “Dunk heard Farmer Gill's legend of Sir Brandon and kept him drinking on his porch all evening.” Its other scene candidates are low-value or represented by selected items. Session 002's added encounters cover the faun exchange and Uriah's conversation with Ingrid. Mule remains absent from Goals. These are observations awaiting user review, not new quality verdicts.

The first Session 001 Summary-writing response omitted selected fact_8. Only writing was retried with unchanged inputs/prompts; originals are retained in runs/s001/attempts/initial-step6/. The retry validated and the Recap completed. Session 002 required no retries. No schema, prompt or implementation change was made during generation; implementation hashes match the pre-run snapshot.

[Generation verification](generation-verification.json) passed for historical accounting/focus/representatives, classifications, source citations, prior-state accounting, selection replay, input/implementation hashes, asset exclusion, exact copies, full-text source views, Recap counts/limits and links. Remaining unjudged issues include possible overlapping potion-plan bullets in Session 002; no semantic retuning or manual deletion was applied. Other output differences can reflect ordinary model variation, not just the historical change. See review run-notes.md. The low-stakes filter and low-impact/high-lasting experiments remain deferred.
