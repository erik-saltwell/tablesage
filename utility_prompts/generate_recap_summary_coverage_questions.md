<overview>
Generate a review-ready list of closed-ended coverage questions from an existing TableSage Recap Summary.

The questions define the facts that a revised recap must retain. The output is an intermediate artifact for human review, not a claim that every detail in the recap is equally important.
</overview>

<source_contract>
- The sole source is one existing Markdown Recap Summary.
- Use only facts stated in that recap. Do not add Ledger facts that the recap omitted.
- Each bullet may contain scene context and one or more substantive claims. Scene context is not independently required unless it is needed to understand a claim.
</source_contract>

<selection_policy>
- Extract consequential developments: discoveries, decisions, outcomes, durable changes, gains, losses, threats, and unresolved situations.
- Prefer one or two substantive facts per scene when the recap supports them.
- Exclude decorative wording, routine movement, incidental method, generic atmosphere, and redundant explanation.
- Split independent consequential claims into separate questions. Keep tightly coupled action and outcome together when a reviewer would naturally retain or remove them together.
- Preserve attribution and uncertainty when the recap presents a statement as a report, belief, rumor, or plan rather than established truth.
</selection_policy>

<question_rules>
- Every question must be closed-ended, standalone, and answerable "yes" from the recap alone.
- Each question must test one fact that should be mandatory if retained after review.
- Include location or scene context only when it disambiguates the fact.
- Use natural wording. Do not mention the recap, bullet numbers, or source text.
- Do not impose a minimum or target number of questions.
</question_rules>

<output_format>
Return only valid JSON with exactly this shape:

{
  "questions": []
}

All values in `questions` must be non-empty strings. Do not include markdown, comments, explanations, candidate tiers, or additional keys.
</output_format>
