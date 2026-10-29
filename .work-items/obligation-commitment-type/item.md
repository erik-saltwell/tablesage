---
name: "Obligation commitment types"
status: complete
---

# Obligation Commitment Types

Add required `commitment_type` classification and exclude general agreements from published obligations while retaining unfiltered generation evidence. The current approved taxonomy is `general_agreement`, `personal_promise`, `debt`, `bargain`, `assigned_duty` and `oath`, superseding the original four-type implementation and replacing `business_contract` with `bargain`. Preserve the existing lifecycle, burden and consequence filters.

The prompt distinguishes actual sworn oaths from casual promise/vow wording, and explains overlapping types. Existing saved artifacts require regeneration; do not backfill inferred types or regenerate production data as part of this source change. The shared nested schema carries the field into Post-Session Matters.

No quality rubric was defined; proceeded with the explicit implementation request. See [the updated contract](../port-tablesage-matters-artifacts/specification.md). Verification passed: Ruff for the changed Python module; whole-project `ty check --output-format concise`; direct schema/filter execution over 320 combinations with 27 retained; missing/unknown type rejection; Post-Session Matters assembly preserves all six fields and order. The disposable in-memory assembly used Session 002 source data and supplied fixture-only Opportunity titles for the separate existing schema change. No production files were changed, no model calls were made, and no unit tests were added or expanded. Source changes are complete; deployment and production regeneration were not requested.

## Adopt Six Commitment Types

The user explicitly approved adopting the previously trialed six-type taxonomy and excluding trivial stake. Update the schema, prompt guidance and examples, and current artifact contract. Ordinary promises are distinct from general agreement; bargains include noncommercial exchanges; assigned duties require accepted bounded responsibilities. Existing `business_contract` records require regeneration through normal freshness handling, with no automatic relabeling. Verification passed: Ruff on the changed Python module; whole-project type checking; targeted whitespace checks; direct schema/postprocessing/filter checks over 1,920 combinations with 135 retained; legacy and unknown enum rejection; preservation of unfiltered entries, retained fields and order; combined Post-Session Matters assembly; and packaged prompt rendering with all six definitions. No unit tests, model calls, deployment or campaign regeneration were performed for this follow-up.
