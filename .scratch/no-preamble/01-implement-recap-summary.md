# Implement Recap Summary

## Problem / desired outcome

Generate a compact, human-readable recap of the current Session as its own artifact. The recap
must describe only the current Session and must be useful independently as well as when inserted
into the following Session's composed full Summary.

The Recap Summary is deliberately separate from full Summary generation so that its prompt and
behavior can be optimized and evolved independently.

## Inputs and generation

- Generate the Recap Summary with its own LLM call and prompt.
- Use the existing `llm_model_high` setting; prompt identity and optimization remain independent
  from the other generators.
- Supply the Session context and the canonical Ledger as inputs. Session context includes the
  campaign name, game system, Session date, attendees and roles, and campaign glossary.
- The Ledger is the sole source for claims about what happened during the Session. Session
  context supplies names and orientation, not additional events.
- Run this phase whenever **Generate Outputs** runs, after Ledger generation succeeds.
- Make one application-level generation attempt. Unlike structurally validated outputs, a
  stylistically weak but valid Recap is improved through prompt optimization rather than retries.

## Initial placeholder prompt

The first implementation intentionally uses a placeholder prompt rather than settling the final
Recap Summary format. Instruct the model to:

- produce one Markdown bullet per scene;
- give each bullet a short description of the scene; and
- include a one-sentence summary of what happened in that scene.

The final length, selection rules, voice, and formatting contract remain deferred for later prompt
design and optimization.

## Artifact and composition behavior

- Persist the result as `recap_summary.md` in the Session folder.
- Render it as a reusable Markdown section beginning with `## Recap`.
- Treat it as a first-class, user-visible and exportable Session artifact.
- Insert the completed section verbatim at the full Summary generator's required
  `<!-- RECAP -->` marker when deterministically composing the following Session's `summary.md`.
- Select the previous Session within the campaign by date, with sequence number as the same-day
  tiebreaker. Undated Sessions follow dated Sessions and use sequence number among themselves.
- Remove the marker without adding a Recap for the campaign's first Session. If a previous Session
  exists but its Recap artifact is missing, fail Summary generation.
- Do not automatically invalidate a following Session's Summary when this Recap changes; that is
  the user's responsibility for now.
- Generate and replace the artifact atomically. A failed call must not leave a partial file.
- Invalidate it whenever its Ledger source becomes stale or is replaced.

## Acceptance criteria

- Recap Summary generation uses a dedicated prompt and LLM call, separate from Ledger and full
  Summary generation.
- The prompt receives Session context and the complete canonical Ledger.
- The initial prompt requests exactly one short, one-sentence Markdown bullet for each scene.
- A successful call writes a normalized `recap_summary.md` beginning with `## Recap`.
- The artifact appears in Session Detail and can be exported directly.
- **Generate Outputs** regenerates it every run after successfully regenerating the Ledger.
- Full Summary composition replaces exactly one `<!-- RECAP -->` marker with the previous
  Session's persisted recap section, or removes it for the first Session.
- Tests cover prompt inputs, normalization, atomic replacement, invalidation, Generate Outputs
  ordering, artifact visibility/export, and deterministic marker replacement.

## Deferred decisions

- Final recap length and number of bullets.
- Final inclusion and omission rules.
- Final prose voice and detailed Markdown presentation.
- Prompt evaluation criteria and optimization dataset.

## Implementation context

- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/`
- `packages/tablesage-application/src/tablesage_application/paths.py`
- `packages/tablesage-application/src/tablesage_application/application.py`
- `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py`

## Triage state

`ready-for-agent`
