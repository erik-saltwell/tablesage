# Documentation guides plan

Build ten task guides that take a GM from a stated starting point through concrete actions to a recognizable result. Separate campaign setup from new-player processing because the processing branch depends on usable voice prints, rather than campaign age. Keep session output generation separate from campaign preparation, while linking the workflows.

## Inspected sources

- `docs/guides/`, the session-processing concepts, and the screen references.
- TUI campaign, session, export, player, transcript-review, new-speaker, Previously On, and Opportunities screens; processing steps and coordinator.
- Application session entities and attendance seeding, processing-step definitions, campaign history validation, and artifact generation dependencies.

## Work

- [x] Write the six missing task guides: campaign setup, both processing workflows, correction/recovery, glossary maintenance, and workspace transfer.
- [x] Revise the existing output, voice-recognition, preparation, and settings guides to fit the task navigation, preserving useful existing detail and incoming links.
- [x] Update the Guides index and README navigation; point the broader public-documentation handoff at this separate work item.
- [x] Verify local links, anchors, images, all ten index entries, and behavior claims against the code. Review the final source changes for scope and Markdown formatting.

No application code, unit tests, site publication, or fresh screenshot capture is required. Existing images may be reused where they clarify the task. There is no rubric; implementation proceeds under the user's explicit request, with qualitative dimensions unassessed. No MkDocs configuration currently exists, so verification uses source/link checks rather than a site build.
