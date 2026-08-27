# Deepen the Summary Generation Module

## Overview

Concentrate the complete file-backed Summary use case in the Summary generation module. `Application` continues to resolve the Session and load campaign Glossary data, then delegates generation as one operation.

## Responsibilities

`Application` retains:

- Session and Campaign lookup.
- Database access for Glossary entries.
- Supplying configured model values.

The Summary module owns:

- Generation eligibility from the current role-transcript source.
- Role-transcript and Summary artifact paths.
- Deterministic Glossary prompt preparation.
- Prompt rendering and LLM invocation.
- Plain-Markdown validation and normalization.
- Atomic replacement of `summary.md`.
- Preservation of an existing Summary on failure.

## Flow

1. The TUI asks `Application` whether Summary generation is available.
2. `Application` resolves the Session folder and delegates the check to the Summary module.
3. For generation, `Application` loads the campaign Glossary and delegates once.
4. The Summary module reads the role transcript, prepares prompt data, calls the LLM, validates the response, and atomically replaces the Summary.
5. Failures leave the prior Summary unchanged.

## Rules

- The Summary module remains in `tablesage-application` and does not query SQLite.
- The current source is `transcript_roles.md`, but source selection stays local to the module so it can change later.
- The shared application LLM helper remains the LLM seam.
- Structured output is not used.
- `processing.can_generate_summary` is removed; eligibility lives beside generation.
- Tests exercise eligibility and generation through the Summary module's public interface.
