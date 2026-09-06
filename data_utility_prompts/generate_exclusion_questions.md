<overview>
Generate candidate exclusion questions for evaluating a tabletop-RPG Ledger or Summary.
</overview>

<inputs>
You will receive a session transcript containing in-fiction play mixed with table talk, game mechanics, and other chatter.
</inputs>

<goal>
Return only closed-ended yes/no questions about content that a polished Ledger or Summary should omit. The questions will be asked of
the generated Ledger or Summary: any question it can answer indicates excluded content leaked into the output.
</goal>

<include>
Generate questions only for distinct excluded concepts that are explicitly supported by the transcript:

- Rules discussion and mechanical procedure: dice rolls, target numbers, modifiers, bonuses, damage calculations, initiative,
  turn order, attack resolution, saving throws, character-sheet statistics, classes, levels, experience points, and resource
  bookkeeping as game procedure.
- Out-of-character chatter: real-world jokes and references, sports or media discussion, scheduling or administrative talk,
  commentary about the game or players, meta-gaming, and strategy that was discussed but never established as fictional action.
</include>

<exclude>
Do not generate a question about:

- The fictional effect or outcome of a mechanical action. Preserve an accidental injury, discovery, escape, or other story result;
  exclude how a die roll or rule produced it.
- Named in-fiction actions, spells, abilities, dialogue, or events. A name that hints at a game system is still retainable when it
  describes what happened in the fiction.
- Ordinary in-fiction quantities such as payments, prices, dates, distances, item counts, or supplies, unless the transcript is
  discussing them as game procedure or bookkeeping.
- A statement that explicitly establishes or revises the fiction, even if it was spoken out of character.
</exclude>

<question_rules>
- Every question must be answerable "yes" from the transcript alone.
- Use speaker-neutral wording. Prefer "someone", "the group", or passive voice; never name a player, character, or Game Master.
  The metric tests whether excluded content leaked, not who said it.
- Ask one question per distinct excluded concept. Do not split one rule explanation into overlapping questions about each number or
  modifier, and do not repeat the same excluded topic in different wording.
- Include enough detail to distinguish the excluded concept from an unrelated narrative event, but do not require exact speaker
  attribution.
- Return an empty list when the transcript contains no qualifying excluded content.
</question_rules>

<output_format>
Return only valid JSON with exactly one key, "questions", whose value is a list of strings. Do not include markdown, commentary,
or any additional keys.
</output_format>
