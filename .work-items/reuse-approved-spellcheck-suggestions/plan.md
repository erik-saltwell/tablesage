# Implementation plan

Implement the agreed behavior in [intent.md](intent.md), using the three approved quality dimensions in [rubric.md](rubric.md). Numerical anchors remain undefined; the user's explicit implementation request proceeds with that gap noted.

- [x] Persist campaign correction memory in the campaign folder; seed once from saved spellcheck decisions and merge matching memories with LLM suggestions. Verify cross-session matching, seeding, forgetting, and campaign export.
- [x] Preserve removed correction rows and edits across drafts and completed spellcheck reviews; update memory only for new committed decisions. Verify duplicate grouping, case sensitivity, and unchanged old reviews.
- [x] Preserve removed transcript utterances and committed Find/Replace mappings across drafts and completed reviews. Verify output excludes removed rows while reopened reviews can restore them.
- [x] Run focused lint, type checking, existing relevant tests, and direct behavior checks. Record outcomes and remaining limitations.
