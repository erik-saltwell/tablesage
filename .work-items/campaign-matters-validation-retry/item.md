---
name: "Retry invalid campaign Matters responses once"
status: complete
---

# Retry Invalid Campaign Matters Responses Once

When a campaign Matters response fails JSON decoding, schema validation or response normalization/link checks, allow one fresh model call. A second invalid response raises its validation error. Apply to all ten Matters categories; preserve each returned raw attempt in `.generation-records/` before validation. Publish only a valid selected response and its matching unfiltered evidence. Transport/authentication, cancellation and filesystem failures are not part of this retry policy. Failed attempts may reserve permanent IDs; existing never-reuse semantics retain those gaps.

The deployed `generate_artifacts.matters_validation_retries` defaults to 1 and accepts 0 to disable. Values above 1 are disallowed. Application supplies it explicitly, fingerprints it for Matters consumers and does not forward it as a provider option. Existing settings gain the default without editing workspace settings. No schema, prompt, dependency-scoping redesign or campaign regeneration is included. The shared code/Application fingerprints still cause normal broad invalidation; finer invalidation is separate work.

No engineering quality rubric was defined; proceed under the user's explicit implementation request. Implementation and verification are complete. See [the Matters contract](../port-tablesage-matters-artifacts/specification.md).

## Verification

Passed 22 offline behavioral scenarios using the actual generator with a replayed model transport and disposable Campaign/Session folders. These cover recovery from schema errors for all ten Matters categories; the exact rejected Session 004 response followed by success; two invalid responses; malformed JSON recovery/exhaustion; invalid link recovery; immediate success; disabled retries; first-call and retry-call transport failures; cancellation; raw-evidence write failure; publication failure; unchanged old publication/evidence on failure; separate raw attempt files; unchanged request inputs/options; and correct successful normalized evidence. No real model calls or production output changes were made. Settings checks confirm one retry for existing/deployed configurations and reject negative, above-one, boolean and string values.

Ruff on all three changed Python modules, whole-project `ty check --output-format concise`, targeted whitespace checks and wheel build/inspection pass. Wheel inspection confirms packaged settings, Application injection/fingerprint and producer retry code. No unit tests were created or expanded.

Offline evidence: [/tmp/tablesage-matters-retry-verification-5rn8pe0t/report.json](/tmp/tablesage-matters-retry-verification-5rn8pe0t/report.json). Wheel: `/tmp/tablesage-matters-retry-wheel/tablesage_rpg-1.0.1-py3-none-any.whl`. Live provider behavior is unassessed; deployment and campaign regeneration were not performed.
