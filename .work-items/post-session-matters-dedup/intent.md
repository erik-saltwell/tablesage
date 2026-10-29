# Remove Duplicates in Post-Session Matters: Intent

## Intended Outcome

Remove items that repeat the same content across Matters categories from the assembled Post-Session Matters output, and so from the Session Summary built from it. An LLM identifies which items other items already cover, and deterministic code removes the redundant copies. Readers and listeners then get each piece of information once. Nothing they need is lost.

The working direction comes from the workshop recorded in [idea.md](idea.md). The decisions below were settled with the user on 2026-10-27.

## Scope

- **Cross-category repeats:** Remove an Open or Historical Matters item when items in other categories already state its content.
- **Assembled output only:** Removal applies only to `post_session_matters.json`. The ten individual Matters artifacts are unchanged, because extractors and later Sessions read them.
- **Excluded: Present Matters.** `current_position`, `present_danger` and `immediate_goals` are never removed and never count as coverage. The user accepts that Present Matters may repeat other items.
- **Excluded: repeats within one category.** These were not identified as the problem.

## Expected Behaviour

1. **Matters Coverage (new hidden LLM artifact):**
   - Reads this Session's nine Open and Historical Matters.
   - For each item it judges redundant, records the other items that together already state everything in it.
   - Code labels items for the prompt by category and position (for example, `obligations[0]` and `developments[2]`), because most categories have no IDs, and maps the response back to those references.
2. **Post-Session Matters assembly (remains deterministic):**
   - Reads the Matters and Matters Coverage.
   - Applies the removal rules.
   - Logs each removal, naming the removed item and the items covering it.
   - Regenerating Post-Session Matters never calls an LLM, so changing the rules can be tried again without another LLM call.
3. **Removal rules:**
   - An item is removed only when every item covering it belongs to a higher-ranked category.
   - An item is never removed while one of the items covering it is also being removed. Categories are processed from the top down.
   - Code drops any coverage claim that breaks these rules, such as a claim pointing at the same rank, a lower rank or a reference that does not exist. It logs the dropped claim and applies the other claims.
4. **Category order:** Open Matters rank above Historical Matters, because Players act on what is still live. More specific and actionable categories rank higher.
   - **Open:** Obligations > Opportunities > Goals > Goal Impediments > Brewing Troubles > Mysteries.
   - **Historical:** Revelations > New Assets > Developments.

## Contract Changes

These change the [Post-Session Matters specification](../post-session-matters/specification.md). That specification currently says assembly makes no LLM call and changes no data.

- **New dependency:** Post-Session Matters depends on Matters Coverage as well as the ten Matters. A change to Matters Coverage makes Post-Session Matters stale. Matters Coverage depends on the Matters it reads and on its prompt.
- **Model and settings:**
  - Matters Coverage uses `llm_model_high`.
  - It reuses the existing `generate_artifacts` settings `matters_effort`, `matters_validation_retries` and `timeout`. Nothing is hardcoded.
- **Failure:** If Matters Coverage fails or does not validate, Post-Session Matters is not produced. There is no fallback to output with duplicates left in, which matches the existing rule of no partial results.
- **Session Summary:** No new link is needed. It already reads Post-Session Matters, so it gets the deduplicated content and becomes stale when Matters Coverage changes.
- **Table Recap:** The paused Table Recap step does not change. When its replacement is designed, it must read the deduplicated Post-Session Matters, not the individual Matters.

## Verification

Check the result manually on real Sessions after it is built. Start with the Session in the 2026-10-27 deployment backup (`~/data/tablesage-deployment-backups/20261027T195011Z-001-immediate-goals/`), which contains the Quinn and Lady Hilda repeats.

- Read the removal log alongside the original Matters, and judge the result against the rubric. The most important check is Information preservation: no removed item held a fact that is now missing.
- If the LLM misjudges coverage, adjust the prompt first. If that is not enough, reconsider the deferred fact-by-fact coverage described in [idea.md](idea.md#deferred-and-rejected-options).
- No automated test suite is added, in line with the project verification policy.

## Acceptance Conditions

- In the 2026-10-27 Session, a Development that is fully covered by higher-ranked items is removed, as the Quinn Development is expected to be. The items that cover it remain.
- No Present Matters entry is removed.
- No item is removed in favour of an item from the same category or a lower-ranked one.
- Every removal and every dropped coverage claim appears in the log, with the references involved.
- Regenerating Post-Session Matters alone makes no LLM call.
- The individual Matters artifacts are unchanged.

## Unresolved Questions

- **Coverage reliability:** Whether the LLM judges coverage reliably is unknown until the manual check above has been carried out.

## Quality Rubric

Approved 2026-10-27. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the deduplicated Post-Session Matters output and how it was produced.

- **Redundancy removal:** Content the reader has already seen in another category doesn't appear again. This rewards catching real cross-category repeats, including ones that are worded quite differently.
- **Information preservation:** Nothing the reader needs disappears. If an item overlaps another but adds a fact, stake, consequence or framing that matters, it stays. This dimension is in tension with Redundancy removal: an aggressive approach does well there and badly here.
- **Best home for the survivor:** The copy that remains is in the category where the reader gets the most from it. For example, something the Players can act on is kept as an Opportunity rather than as a past Development. This is separate from the first two dimensions, because an approach can remove exactly the right number of items and still keep each fact in the weaker category.
- **Traceability:** It is possible to see which items were treated as duplicates, which one was kept, and why. The user specified that logging should provide this. This is separate from correctness: an approach can make perfect removals that nobody can check, or make mistakes that are easy to spot and fix.
