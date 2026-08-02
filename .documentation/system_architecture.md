# TableSage system architecture

TableSage is organized into four layers. The structure keeps the user interface thin, makes use cases testable, and preserves reusable audio/provider capabilities.

```text
tablesage-tui → tablesage-application → tablesage-model
                                     → tablesage-tools

tablesage-model → no project packages
tablesage-tools → no project packages
```

## `tablesage-tui`

The Textual user interface. It presents data, collects input, renders progress/errors, and invokes application use cases. It does not access SQLite repositories or media/provider adapters directly.

## `tablesage-application`

The orchestration layer. It implements use cases such as campaign management, session processing, voice-profile seeding/enhancement, transcript review, and summary generation.

Application use cases validate inputs, own transaction boundaries, coordinate repositories and tools, emit progress, and return UI-friendly results. They depend on repository interfaces, never on a concrete SQLite implementation.

Organize this package by use case rather than technical helper type, for example `campaigns`, `sessions`, `voice_profiles`, `transcript_review`, and `summaries`.

## `tablesage-model`

The domain and persistence package. It contains domain entities such as campaigns, sessions, players, voice samples, discourse, and summaries; it also defines repository and unit-of-work interfaces.

SQLite is initially implemented here, but behind an explicit internal seam:

```text
tablesage_model/
  domain/       domain entities and invariants
  repository/   repository and unit-of-work interfaces
  sqlite/       SQLModel mappings, SQLite repositories, Alembic migrations
```

The SQLite adapter must not leak SQLAlchemy/SQLModel sessions through repository interfaces. This makes moving `sqlite/` into a separate package possible later without changing application use cases.

## `tablesage-tools`

Independent media and provider adapters. It includes audio conversion/cleaning/clipping, transcription and diarization providers, embedding extraction, similarity calculation, centroid computation, and text post-processing.

Tools operate on generic inputs, outputs, and explicitly supplied paths. They do not know about TableSage campaigns, players, voice-sample provenance, database records, application filesystem layout, or `AppSettings`.

Tools may compute embeddings and centroids. The application/domain layers decide whether a result becomes a player voice profile, which clips are accepted, and how provenance is persisted.

## Composition and testing

The executable composition root constructs concrete SQLite repositories and tool adapters, then injects them into application use cases. This is the only place that knows all concrete implementations.

- Test domain invariants without SQLite or provider dependencies.
- Test application use cases with fake repositories and fake tools.
- Test tools against adapter contracts and provider/media fixtures.
- Test SQLite repositories and Alembic migrations as integration tests.
