---
name: "Obligation recipient stake"
status: complete
---

# Obligation Recipient Stake

Add required `stake` to every obligation, with `trivial`, `low`, `medium` and `high` ratings for the recipient's demonstrated interest in the specific promised performance. The system prompt defines classification anchors and examples, distinguishes a broad outcome from a preferred method, and keeps stake independent of burden, consequence and commitment type.

The user requested this field and a rubric for its values. The user subsequently approved excluding `stake: trivial` while retaining `low`, `medium` and `high`, alongside adoption of the six commitment types. Existing lifecycle, burden, consequence and general-agreement exclusions still apply. No quality rubric was defined for the engineering work; proceed with the explicit implementation request.

The source schema automatically propagates the required field to Post-Session Matters. Existing saved records require regeneration; no production data migration, deployment or model generation is included. See [the current contract](../port-tablesage-matters-artifacts/specification.md). Verification passed: direct schema validation accepts all four stake values and rejects missing, unknown and null values; all four ratings survive the unchanged publication filters; Post-Session Matters assembly preserves the field and ordering. Assembly used disposable in-memory Session 002 data with fixture-only Opportunity titles for the separate existing schema change. Whole-project type checking and targeted diff whitespace checks passed. No model calls, production artifact writes, or unit-test additions were made.

## Specific-Performance Clarification

Following the Session 002 trial, replace the overlapping method guidance with an ordered decision process: identify the exact performance and recipient, require evidence of specific value or reliance, ask whether any recipient interest would remain unmet if the broader goal were achieved otherwise, then rate magnitude. Speculative usefulness alone establishes no stake. Preserve actual reliance on deliveries and escorts. Add a fresh curator/photograph contrast. No schema or filtering changes, stored relabeling, deployment, or new extraction run are included. This follow-up is a prompt clarification; generation behavior remains to be evaluated.

Follow-up verification passed: the packaged prompt loads and renders through the application helper with the new decision process and reliance safeguard; the replaced method paragraph is absent; targeted whitespace checks pass. No model extraction was run, so changed classification behavior has not yet been verified.

## Exclude Trivial Stake

The user explicitly approved a publication filter excluding `stake: trivial`. Raw/normalized generation evidence retains all ratings. Low, medium and high stake remain eligible subject to every existing filter. This source change does not deploy or regenerate campaign artifacts. Earlier verification notes above describe the pre-filter implementation. Verification passed: Ruff on the changed Python module; whole-project type checking; targeted whitespace checks; direct schema/postprocessing/filter checks over 1,920 combinations with 135 retained; legacy and unknown enum rejection; preservation of unfiltered entries, retained fields and order; combined Post-Session Matters assembly; and packaged prompt rendering with all six definitions. No unit tests, model calls, deployment or campaign regeneration were performed for this follow-up.
