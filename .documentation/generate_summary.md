# Generate Session Summary

## Overview

Generate a Markdown summary of a session from its role-attributed transcript and the campaign glossary. The role transcript is the current source, but generation is separated from that storage choice so a future source can replace it.

## Key Concepts

- **Role transcript** — the LLM-facing transcript, with `**Role** - text` entries separated by blank lines and no timestamps.
- **Glossary** — the campaign's terms and optional descriptions, always included as a prompt section.
- **Summary** — unstructured Markdown returned by the LLM and stored as `summary.md`.
- **Log-derived artifact** — output invalidated when a successful transcription replaces its source material.

## Generate Summary Flow

1. Generation is available when the role transcript exists.
2. The application reads the role transcript and the campaign glossary.
3. Glossary entries are ordered alphabetically and combined with the transcript as prompt data.
4. The application renders the summary prompt and makes one LLM call through its standard prompting boundary.
5. An empty or whitespace-only response fails generation.
6. A successful response atomically replaces `summary.md`; a failure preserves the previous summary.

## Behaviors & Rules

- Use the first alphabetical role for an attendee with multiple session roles.
- Preserve utterances attributed to `unassigned speaker`; they do not block generation.
- Render glossary entries as `- Term: description`, or `- Term` when no description exists.
- Include the glossary section even when the campaign has no glossary entries.
- Save non-empty Markdown without interpreting its structure, except to normalize surrounding whitespace and ensure one final newline.
- The summary call returns plain Markdown and does not use structured output.
- The system prompt is a placeholder to be supplied separately.
- A successful transcription deletes every existing artifact categorized as `FROM_LOG`; a failed transcription deletes none.
- Glossary changes do not invalidate existing summaries. Regeneration is an explicit user action.

## Current Integration Constraints

- The application use case owns reading `transcript_roles.md`; the summary prompt layer receives plain transcript and glossary data without knowing their storage location.
- Summary generation uses `tablesage_application.llm.call_llm_with_prompt` with no response model.
