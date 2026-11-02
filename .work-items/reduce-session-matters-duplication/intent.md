# Reduce Duplication across Matters within a Session: Intent

Some developments appear repeatedly across a Session's Matters categories. An LLM phrases the same underlying information to fit each category, producing several entries that add no extra information. The goal is a better summary with less repetition while preserving useful entries and distinct information.

## Intended Approach

Identify the recurring patterns shared by these redundant entries, then develop precise rules for handling each pattern: where the information belongs and how it should be represented. Add an LLM pass when creating Post-Session Matters to apply those rules.

The appropriate result depends on the pattern. Several entries may coalesce into one final Matter, or the result may contain multiple Matters when that produces a better summary. There is no universal rule that a development must appear in exactly one category.

## Scope and Constraints

- Target specific, identified patterns of duplication within a Session rather than giving an LLM a broad instruction to remove anything it considers redundant.
- Preserve good entries and distinct information. Similar subject matter alone does not establish that entries should be collapsed.
- Make each fix precise enough to address the identified pattern reliably. Narrow scope supports both information preservation and clearer instructions to the LLM.
- Keep the approach simple and focused. This is a fresh work item; the earlier deduplication item's design and plan are not adopted.

## Details Still to Establish

The concrete patterns and representative examples are recorded in the [duplication analysis](analysis.md), and each established pattern has its own work item (listed in [item.md](item.md)). The rules for each pattern have not yet been decided. The LLM pass's exact inputs, output contract, placement, and handling of the individual Matters artifacts also remain undecided. Whether within-category splits are in scope is unresolved.

No evaluation has been performed against the rubric below. No implementation is authorized by this intent save.

## Quality Rubric

Approved 2026-10-29. These are qualitative dimensions, judged in words, with no scores, weights or thresholds. The subject is the duplication-reduction work: the patterns identified, the rule written for each pattern, and the Post-Session Matters output those rules produce.

- **Grounded in real Sessions:** Each pattern comes from duplication actually seen in real Session outputs, backed by representative examples, not from guesses about what might repeat. This rewards a solution you can trace back to evidence: for each rule, you can point to the Sessions and entries that prompted it.
- **Narrow, pattern-specific handling:** Each rule targets one identified pattern and makes an explicit decision about it, such as merging the entries into one Matter, keeping several Matters, or moving the information to a particular category. This rewards precise, bounded instructions over a general "remove redundancy" directive. Entries that match no identified pattern are left alone.
- **Pattern resolution:** In the output, the identified patterns actually stop producing repeated entries, and they do so consistently across Sessions. This is separate from Narrow, pattern-specific handling: a rule can be precise and still be applied unevenly by the LLM pass.
- **Information preservation:** No useful information is lost. If an entry overlaps another but adds a distinct fact, stake, consequence or framing, it survives, possibly merged into another entry. Similar subject matter alone is not treated as duplication. This pulls against Pattern resolution: an aggressive pass does well there and badly here.
- **Best representation:** The information that remains is in the category and form where it helps the reader most. That might be one Matter in the right category, or several Matters when that makes a better summary. This is separate from Pattern resolution and Information preservation: an approach can remove exactly the right repeats and keep every fact, yet leave the remaining entry in a weaker category or worded poorly.

Simplicity is deliberately not a dimension. "Keep the approach simple and focused" remains a constraint in the intent, and Narrow, pattern-specific handling already rewards focus at the level of individual rules.
