---
name: "Avoid new obligations already listed in current Matters"
status: complete
---

# Avoid New Obligations Already Listed in Current Matters

Obligations generation receives current filtered Goals, Goal Impediments and Opportunities alongside its existing previous Obligations, party Roles and Scene Log. Move Obligations from the first to the fourth generation wave so these inputs are available. The shared dependency declaration also updates application loading, generation planning and freshness tracking.

The prompt excludes new obligations that repeat the meaning of entries in those three current inputs, while still reconciling previously tracked obligations. Sharing an entity or broader objective alone does not exclude a distinct, independently fulfillable duty. Existing schema and publication filters remain unchanged. The [Matters contract](../port-tablesage-matters-artifacts/specification.md) and public freshness reference reflect the new dependencies.

Verification: targeted Ruff and whole-project `ty check` passed. Direct execution verified packaged prompt rendering with populated and empty current arrays, preservation of previous obligations and Scene Log, rejection of missing current inputs, dependency ordering across all waves, and Obligations ordering before Revelations. `git diff --check` passed. No model calls, campaign artifact regeneration or unit-test additions were performed; model adherence remains unassessed. No engineering quality rubric was defined; implementation proceeded under the explicit user request.
