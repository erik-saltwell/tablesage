# Preferences

What the user wants in Campaign Matters, the Session Summary and the Table Recap, either stated outright or inferred from reactions to output. A preference is kept even when the current prompts already encode it. Superseded preferences are kept and marked, because goldens and older examples were judged against them.

Each entry records its scope, its evidence type (`stated`, `reaction` or `both`), a verbatim quote, where it is encoded today and its examples. "Encoded in" paths use `st:` for `~/data/tablesage_summary_test/artifacts/prompts/campaign-matters/<matter>/system.md` and `pt:` for `~/proj/tablesage/packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_matter_<matter>/system.md`.

## Cross-matter

### PREF-014
**The model classifies; code decides what to keep.**
- Scope: all matters
- Evidence: stated
- Source: SRC-26 (2026-10-23T20:30Z, 2026-10-22T18:02Z)
- Quotes (verbatim):
  > The approach i want to keep is that the llm does not make exlude/keep decisions.  it classifies on a number of dimensions, and i run a deterministic filtering pass on what comes back from the llm

  > I always add the filtering after i run this workflow so that i can see the unflitered results when i run validate.  this is how i decide what to filter.
- Encoded in: every standalone generator filters after validation; prompts say "Retain all qualifying levels … downstream filtering is separate."
- Examples: EX-001, EX-007, EX-017, EX-020
- Approaches: [APP-001](approaches.md#app-001), [APP-011](approaches.md#app-011)
- Applied 2026-11-01 (SRC-58): the user agreed ("Agreed") that the model should list every beat that touches no thread as a standalone history candidate. Code drops the `low` ones and records them in the kept-and-dropped review, rather than the pass 9 thread prompt telling the model to "Leave out `low` beats that touch no thread". The model keeps the definitional exclusion of plain colour and routine. Encoded in [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s thread prompt and `historical_coverage.standalone_split` (2026-11-01); checked with fixtures, not yet with generated output.

### PREF-012
**Prompt examples are fictional and never echo session text.**
- Scope: all prompts
- Evidence: stated
- Source: SRC-32 (2026-10-25T03:38Z, 03:41Z)
- Quotes (verbatim):
  > We need to use an example not from our sessions, so we can test correctly

  > I actually want the prompt for now to not mention people having other problems, that is too close to the session text
- Why: an example built from test-session text lets the prompt memorize the answer, so a test run no longer shows whether the rule generalizes.
- Encoded in: practice across all prompts, for example the archivist, ferryman and sealed-observatory examples.
- Examples: EX-014

### PREF-004
**Each entry carries only its own category's angle; the same content is not restated across categories.**
- Scope: all matters, as assembled into the Summary and Recap
- Evidence: both
- Source: SRC-51 (2026-10-29T16:37Z), SRC-53, SRC-01 (the golden)
- Quote (verbatim):
  > some kind of developments seem to show up in many post session matters, and they don't seem to add any extra information. They are just things that could apply in multiple matters, so the llm phrases it in ways appropriate for different matters and they end up all over the place.
- Refinement: sharing a subject is fine when each entry adds something (EX-025, EX-026). Restating the whole item under another category's heading is the defect.
- Encoded in: prompts allow "the same subject across categories when each captures a distinct meaning". Several prompts receive upstream matters with do-not-repeat guidance, for example Obligations receiving Goals, Impediments and Opportunities (SRC-43). Duplication persists in output (EX-003, EX-021 to EX-024).
- Examples: EX-003, EX-021, EX-022, EX-023, EX-024, EX-025, EX-026

### PREF-015
**Matters answer three questions: what happened, where are we, and what's ahead. Overlap between "what happened" and "what's ahead" is legitimate but has a cost.**
- Scope: all matters, Summary, Recap
- Evidence: stated
- Source: SRC-55 (2026-10-29T18:24Z, 18:32Z, 18:47Z)
- Quotes (verbatim):
  > there are good reasons to keep in both Developments and at least one Open Matters.  So in a way i am saying that it is both a problem and not a problem

  > - previous matters: what happened?  (btw i am unconvinced that new assets and revelations are earning their keep beyond developments.  I am not looking to kill them, just know i am on the fence.   particularly new assets)
  > - current matters: Where are we?  Current situation and current (?) danger
  > - open matters: What's ahead? Goals, impediments, opportunities, mysteries, and obligations (and of all of these, i am on the fence about obligations)

  > Is it possible that there are four steps in this unified flow? One, determine what's true, which is the creation of threads and facts. Two, determine what to keep. Three, determine where it goes. And four, determine how to phrase it.
- Also stated: the user is on the fence about New Assets and Revelations (as separate from Developments) and about Obligations.
- Encoded in: the in-progress Unified Matters Pipeline ([APP-034](approaches.md#app-034)).
- Examples: EX-003, EX-025

### PREF-017
**Present Matters may repeat other items.**
- Scope: present-matters
- Evidence: stated
- Source: SRC-42 (2026-10-28T00:07Z)
- Quote (verbatim):
  > (b)  I am ok if present matters duplicates something in previous/open matters
- Examples: EX-021

### PREF-018
**Redesigns are built side by side and replace the existing artifacts only once their quality is proven.**
- Scope: Summary, Recap and any replaced artifact
- Evidence: stated
- Source: SRC-55 (2026-10-29T20:47Z)
- Quote (verbatim):
  > I just want to be able to compare side by side because the existing artifacts are great in many ways and outside of the duplicate issue I want to make sure that we retain all the goodness we had prior.
- Approaches: [APP-034](approaches.md#app-034)

## Session Summary and Table Recap

### PREF-050
**Keep a detail only if the players would miss it next Session, or it would change what they do later.**
- Scope: summary (every section), recap
- Evidence: the agent proposed the test and the user approved and restated it (SRC-58)
- Source: SRC-58 (2026-11-01)
- Quote (verbatim):
  > Yes, I like this. Would the players miss it or would it change their behavior in the future? Kind of a rule.
- Meaning: cut a second event that only adds what else happened, and a description that only says what someone or something is like. The test applies to every section, so a cut detail should not reappear elsewhere. For example, pass 9 moved "Trout put Dirk under Squints" (EX-078) from history into "Where you are". This generalizes [PREF-007](#pref-007) beyond knowledge. Encoded in [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s writing prompt (2026-11-01), replacing pass 9's recruitment-specific rule; not yet checked against generated output.
- Examples: EX-078, EX-047, EX-059, EX-063

### PREF-049
**Name a person, and add one short identifying role only when they are new or rarely mentioned and the role matters to the event. Provisional.**
- Scope: summary (every section), recap
- Evidence: the agent recommended this and the user approved it, after asking for a recommendation (SRC-58)
- Source: SRC-58 (2026-11-01)
- Quotes (verbatim):
  > Do you have a recommendation here? I'm having a hard time making up my mind.

  > It does. I think that we can keep this, but I would note that we should be on the lookout for if in future runs I give feedback about it in case the cost of the extra complexity and length of the summary turns out to be too high a cost to pay for the benefit. And if it turns out that I believe that just hearing the character's name again is enough of a recognition cue.
- Rule: work the role into the sentence naturally ("Quinn, who owns the Golden Egg, …"). Never stack two labels in one sentence. Never add descriptive traits such as weapons, looks or temperament, which are a profile (EX-047). Familiar names go bare.
- Why (agent's reasoning, accepted): the Summary is heard a week later, and a bare new name gives the listener nothing to attach it to. The EX-057 golden already works this way: titles such as "Eric the Reeve", bare familiar names, and a natural clause ("whom he blames for stolen ale") instead of stacked labels. The fault in EX-078's "Golden Egg owner Quinn … rival tavern keeper Bentley" is the stacking.
- **Watch:** provisional. If future feedback shows the extra length and complexity cost more than they help, or that hearing the name again is enough of a cue, revisit this in favour of bare names.
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s writing prompt (2026-11-01), replacing pass 9's direct use of the Session 001 labels. Not yet checked against generated output.
- Examples: EX-078, EX-057, EX-047

**Pass 12 reconsideration (2026-11-01, SRC-60):** when reviewing Ned’s “a murderous thief” aside, the user tentatively finds a brief descriptor acceptable on the first mention in the current Summary, even for a familiar character. This qualifies the provisional “Familiar names go bare”/no-traits rule; do not enforce it as an absolute failure for this occurrence or turn the tentative allowance into a mandatory descriptor. Exact feedback: EX-080 pass 12 presentation clarification.

### PREF-048
**"Last session..." names the event; specifics such as amounts and conditions belong to the open bullet. A minor issue.**
- Scope: summary ("Last session..." versus the open headings)
- Evidence: stated (SRC-58), choosing between options the agent offered
- Source: SRC-58 (2026-11-01)
- Quote (verbatim), choosing "history should name the event ('offered a bounty') and leave specifics like amounts and conditions to the open bullet":
  > B - It was a small lapse; I did not flag, but this is also a relatively smaller issue compared to the other things we have discussed so far.
- Meaning: when a history bullet and an open bullet share a deal, history tells that it happened ("Eric the Reeve offered a bounty for the dragon"), and the open bullet carries the amount, terms and what remains. Sharing the subject is the legitimate overlap of [PREF-015](#pref-015); repeating the specifics is the lapse. The EX-057 golden's "Quinn promised Sir Phidipaldi 100 gold…" beside the goal's "collect his promised 100 gold" is such a lapse, which the user says was minor and unflagged. EX-057 remains the golden.
- Weight: the user rates this as smaller than the opportunity and duplication problems.
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s writing prompt, whose skiff example no longer repeats the term (2026-11-01). Pass 9's example kept "by dawn". Not yet checked against generated output.
- Examples: EX-057

### PREF-021
**Spoken recap content is short bullets the GM can paraphrase, and rarely uses narrative 'box text'.**
- Scope: recap, summary
- Evidence: stated
- Source: SRC-44 (2026-10-28T17:20Z), SRC-45 (2026-10-28T23:01Z)
- Quotes (verbatim):
  > Box text is universally reviled because read text SOUNDS horrible to listen to - like listenting to someone read a speech while looking down at the text.  players tune out and lose attention. This is why i want the text to be bullet lists - easier to paraphrase and shorter if read.  not the dreaded 'box text'
  > I want to leave the last session content as bullets because otherwise it just becomes a big wall of text that nobody is good at reading.
- Examples: EX-027

**Open-matter continuity clarification (2026-11-01, SRC-60, EX-027):** the user expressly wants still-open matters to remain in subsequent Session Summaries. Unchanged wording is acceptable and does not justify omission or cosmetic rewriting. This supersedes the earlier repetition-only concern for eligible open matters, not within-Summary duplication or lifecycle filtering.


### PREF-023
**When capturing something about all the session's attending party members, the SessionSummary says "the party"; the Table Recap is reframed to "you".**
- Scope: summary, recap
- Evidence: stated
- Source: SRC-44 (2026-10-28T22:12Z), SRC-45 (2026-10-28T23:01Z)

### PREF-024
**Sentence case everywhere, with listenable headings.**
- Scope: summary, recap, all matter titles
- Evidence: stated
- Source: SRC-44 (2026-10-28T17:44Z, 19:36Z, 19:37Z)
- Quotes (verbatim):
  > * "Previously" --> "Last Session..."
  > Otherwise i like all of these.

  > No please use the sentence casing
- The approved heading set (assistant's summary, 2026-10-28T19:37Z): "Last session..., You learned, You gained, Your goals, Standing in your way, What could help, Still unanswered, Promises and debts, Meanwhile, As we return, The danger right now."
- Encoded in: every pt matter prompt ("Use sentence case: capitalize only the first word and proper nouns.").
- Examples: EX-031

### PREF-025
**Child bullets read naturally after their heading.**
- Scope: summary, recap
- Evidence: stated
- Source: SRC-44 (2026-10-28T17:51Z)
- Quote (verbatim):
  > we need to update children bullet lists so they are all phrased to sound natural when read after a heading.  So the heading "You learned"   with a sub bullet that starts with "You learned that"   because that sounds wierd when read

### PREF-026
**Plain, sayable wording, with the small words kept.**
- Scope: all matters as shown in the Summary and Recap
- Evidence: stated
- Source: SRC-46 (2026-10-28T23:22Z), SRC-38 (2026-10-26T20:31Z), SRC-39 (2026-10-27T19:46Z)
- Quotes (verbatim):
  > I want each bullet to be easier to understand on the first reading and easier to say aloud.

  > - **Put the actor and action early.** Make it immediately clear who did, believes, offers, or owes something.

  > I generally like the phraising and structure used. It is just about the dropping of words
- Encoded in: pt `matters-plain-language` (complete). Headline guidance retains articles and small words.
- Examples: EX-033, EX-034

### PREF-027
**Developments are in the past tense and in the order they happened.**
- Scope: developments
- Evidence: stated
- Source: SRC-39 (2026-10-27T20:01Z), SRC-38 (2026-10-26T20:40Z)
- Quotes (verbatim):
  > can you update the developments matter so that it is generated in the past tense?

  > add A directive for the developments prompt that tells the agent to sort them in the chronological order they happened in the game session.

### PREF-028
**An Opportunity's title is one simple sentence combining the opening, the action and the advantage.**
- Scope: opportunities, summary, recap
- Evidence: stated
- Source: SRC-39 (2026-10-27T20:07Z, 20:09Z)
- Quotes (verbatim):
  > I want to add a title property to opportunities that provides a single simple sentience that combines the opening, action and potential advantage into one simple short sentence.  We are currently using just the opening, but in some cases that does not make it clear what the advantage is

  > You should be using the title not just in the table recap but in the post session matters, and then the table recap picks it up from there
- Examples: EX-030, EX-061 (an advantage as vague as "they can see what happens" fails the title's purpose)

**Pass 12 precision clarification (2026-11-01, SRC-60, EX-080):** an opportunity describes the useful action and advantage, not a reproduction of contract details. For offered combat help, “hire him” and “he’ll fight for them” can suffice without the fee or per-kill rebate. The fee is acceptable in historical/Development presentation. Preserve the distinction between concise displayed opportunity wording and the full supported terms in state; this does not authorize inventing terms or establish a blanket rule to omit material risk.

**Conditional-format approval (2026-11-01, SRC-60, EX-040):** user approves making opportunity action/advantage presentation explicitly conditional (“If X, Y”), rather than merely preferable, and merging complementary plan components. An essential uncertainty may remain in a second short sentence. Use general rules rather than the approved Session-specific example; implementation deferred until review discussion is complete.

### PREF-029
**The header of the Session Summary identifies the session: campaign name, session date and session cue.**
- Scope: recap, summary
- Evidence: stated
- Source: SRC-39 (2026-10-27T17:47Z, 18:07Z), SRC-55 (2026-10-29T20:58Z)
- Quotes (verbatim):
  > Can you pass in the campagin name to the j2 template, and change "Last time:" to "Prevously on <campaign-name>:"

  > - Session Date - used in header / title
  > - session Cue - I think we generated this previously it is the most memorable scene cue if i remember  I also want to put this in the Header
- Later: the "Previously" heading became "Last session..." ([PREF-024](#pref-024)). The session cue should eventually appear in the Session Summary.


### PREF-031
**The immediate danger section is reserved for immediate, genuine threats.**
- Scope: present-matters, summary, recap
- Evidence: stated
- Source: SRC-44 (2026-10-28T17:44Z, 22:23Z)
- Quote (verbatim):
  > Load the work item to reserve immediate danger for genuine threats.
- Encoded in: pt `summary-immediate-danger` (implemented).


## Goals

### PREF-033
**A Goal is an end wanted for its own sake. It stays active until it is achieved, abandoned, replaced or failed.**
- Scope: goals
- Evidence: both
- Source: SRC-07 (2026-10-19T00:08Z–00:22Z), SRC-01 (the goldens)
- Quotes (verbatim):
  > i want to add another dimension to the rubric, maybe called top-level.   the dimension is judging that all active goals stand on their own as ends and do not ladder up to other goals.

  > update to say a goal remains active until is is achieved, abandoned, replaced or failed.  for example if the goal is "save the boy" and the boy dies, the goal is no longer active
- Also from the golden: serious interest counts and stays tentative ("Dunk is considering buying Seamus the mule from Farmer Gill"). **Superseded 2026-10-30 in part:** serious interest still counts, but the goal no longer says "is considering" (EX-052). One outcome per line, with the defining reward.
- Changed 2026-10-30 (SRC-55, review of pass 4 Session 001), verbatim:
  > the multiple 'is considering' lines are unnecessary. If they don't pursue the goal, it will fall off next time. This is not the place to track how accepted it is

  Also 2026-10-30, verbatim:
  > In general, we should not be including an explanation of "Why" in goals

  > The bit about who fits in the shirt has no bearing on the shirt as a goal.  it is extra detail/precision and should be removed.

  A goal states the outcome only, with no lead or clue in it: "Find the treasure shown on the party's treasure map" was rejected as "this whole map reference is unnecessary" (EX-051). When the party takes up a job, its outcome can be a goal ("there is no goal about catching quinns thief", EX-056).
- Encoded in: the Goals definition. `parent_goal_id` with a code filter on `null`; `significance` with `incidental_goal` filtered out; `open` lifecycle only.
- Examples: EX-035, EX-036, EX-051, EX-052, EX-056, EX-058, EX-059

**Pass 12 severity clarification (2026-11-01, SRC-60, EX-051):** the user reaffirms describing only the goal as a general preference, while judging the map reference in this particular treasure goal “a very minor issue.” Preserve the general outcome-only guidance without overstating this occurrence’s severity or introducing a named-example exception.

### PREF-051
**How a pursuit was established decides how it ends: taken up or agreed pursuits persist until play ends them; floated or one-sided ones lapse unless renewed; episode-local ones end with the episode.**
- Scope: goals, all open matters (lifecycle)
- Evidence: the agent proposed this split from the user's judgments, and the user approved it (SRC-58)
- Source: SRC-58 (2026-11-01); the underlying judgments are from SRC-34, SRC-55 and SRC-57
- Quote (verbatim):
  > Yes I like this
- The three kinds:
  1. **Taken up or agreed:** the party took it up, or both sides agreed to it. It stays open until play ends it: achieved, abandoned, failed, its purpose gone ([PREF-033](#pref-033)'s "save the boy"), or its window passed (EX-070's "the time has passed"). It survives Sessions where it is not mentioned.
  2. **Only floated, offered or one-sided:** an unaccepted challenge (EX-070: "given that the reeve never agreed it was unlikely to ever have lasted beyond the scene anyway"), a purchase being considered (EX-052: "If they don't pursue the goal, it will fall off next time"), or an interest the characters "put down" (EX-072). It lapses unless play renews it, and needs no explicit cancellation.
  3. **Episode-local:** it mattered only within an episode, and it ends when the episode does and the party moves on ([PREF-013](#pref-013), EX-018).
- Why: it replaces challenge-specific rules with the distinction the user's judgments share. It also reconciles "it will fall off next time" with main goals that carry on unmentioned.
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s scene, thread and fact prompts (2026-11-01), replacing pass 9's challenge- and appointment-specific wording. Not yet checked against generated output.
- Examples: EX-070, EX-072, EX-052, EX-018

## Goal Impediments

### PREF-034
**An Impediment is the condition blocking a Goal. An untaken way around it is an Opportunity, and a future obstacle is not shown yet.**
- Scope: goal-impediments
- Evidence: both
- Source: SRC-29 (2026-10-24T22:16Z–22:41Z)
- Quotes (verbatim):
  > I think those are the same impediment for the dragon goal, but the sword one is not an impediment to a goal, it is an opportunity to overcome an impediment.

  > Can you add a new lifecycle value for impediments that are not active yet but will be in the future? Like the flying

  > OK I don't care for that as much, please revert the prompt change
- The last quote is the rejection of the "impedes:" title suffix: the Goal link stays in data.
- Encoded in: Goal Impediments guidance; `goal_ids`; `anticipated`, `resolved` and `obsolete` filtered out.
- Examples: EX-037, EX-038, EX-039, EX-060 (good: "this is good, and what i am looking for in an impediment")

## Opportunities

### PREF-035
**An Opportunity is an actionable opening toward a Goal (required) or around an Impediment (optional). Only top-level openings are shown.**
- Scope: opportunities
- Evidence: both
- Source: SRC-31 (2026-10-24T22:55Z–23:47Z), SRC-08 (2026-10-19T02:51Z)
- Quotes (verbatim):
  > an opportunity represents fundamentally an open window to gain an advantage in either overcoming an obstacle or otherwise increasing their likelihood of achieving their goal. This is inspired by the game Hitman

  > in each case, it has to be something that they have to take action in order to take advantage of.

  > I agree that it needs to tie into a goal.
- Changed over time:
  - On 2026-10-19 a Goal connection was "not necessary". From 2026-10-24 it is required (EX-041).
  - In the 2026-10-18 golden, the window and the potion are separate Opportunities. From 2026-10-24 they are children of the chain-shirt Opportunity (EX-040).
- Form in the golden: "If you X, Y". The later title format is [PREF-028](#pref-028).
- Refined 2026-10-30 (SRC-55), verbatim:
  > An opportunity is an extra action that can be taken to provide an extra advantage in achieving some other goal.

  So a goal's own price or terms ("If Dunk pays Farmer Gill 100 gold, Gill will sell him Shamus.") is not an opportunity (EX-054). Neither is extra detail about an offer already listed (EX-053), nor a weak link between two goals that offers no action (EX-055). A plan for reaching a goal, such as staging a fake ale delivery to catch a thief, is one (EX-056).
- Encoded in: required `goal_id`, optional `goal_impediment_title`, `opening`/`action`/`advantage`/`title`, the `available`/`captured`/`lost`/`obsolete` lifecycle, and `parent_opportunity_id` filtered on `null`.
- Examples: EX-040, EX-041, EX-053, EX-054, EX-055, EX-056, EX-061
- Refined 2026-11-01 by [PREF-045](#pref-045) (when several bullets are one opportunity) and [PREF-046](#pref-046) (the benefit is an advantage, not the goal).

### PREF-045
**One opportunity per plan: an opportunity is "if trigger, then benefit", and three patterns show when several bullets are one opportunity.**
- Scope: opportunities, cross-matter (the unified pipeline's `could_use` openings)
- Evidence: stated (patterns 1 and 2); pattern 3 was proposed by the agent and confirmed by the user
- Source: SRC-58 (2026-11-01), the interview on generalizing the failing prompt checks
- Quotes (verbatim):
  > our current formula for describing opportunities is if trigger, then benefit.

  > two items that share the same trigger but have different benefits should still be described as one opportunity if both benefits are achieving, are making progress on the same goal.

  > Unless those benefits are clearly pointing at two different goals, then they should be wrapped into the same thing.

  > steps in a plan, which can often be identified because you say, if trigger one, then condition two. But then we come back and we say, if condition two, right? So using it as a trigger, then condition three or whatever.

  > you really just want to phrase it as if, you know, the first condition, you know, then we can help get to the, or if the first trigger, then it will generate the final condition we are trying to get to.

  > Yes That is definitely another pattern, and you have correctly identified it.
- The patterns:
  1. **Same trigger, same goal:** two bullets that start from the same action and advance the same goal are one opportunity, with their benefits combined. They stay separate only when the benefits clearly serve different goals.
  2. **A chain is a plan:** when one bullet's benefit is another bullet's trigger, they are steps of one plan. Write it once, from the first trigger to the final condition. [PREF-046](#pref-046), decided later the same day, governs where it ends: at the advantage, never at the goal itself, and a chain splits where it crosses into another goal. The sword example accepted in this interview ended at the goal ("…they can kill the dragon"); under PREF-046 it would end at the advantage.
  3. **Complementary pieces are one plan** (agent's wording, user-confirmed): when two openings each supply part of what one action needs and the party would use them together, such as a way in and an owner kept asleep, they are one plan. When either alone would do the job, they are alternatives and stay separate.
- Boundary: different triggers with different benefits stay separate even when they serve one goal, such as hiring an ally versus retrieving a weapon, or a chart versus passage on a boat ([PREF-041](#pref-041)).
- Why: it replaces judgments of individual pairs with a test that applies to new cases. It came from asking what EX-040's and EX-073's pairs have in common, instead of fixing each pair.
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s resource-reconciliation and facts prompts (2026-11-01), replacing pass 9's disguised copies of the Session 002 pairs. Not yet checked against generated output.
- Examples: EX-040 (patterns 2 and 3), EX-073 (patterns 1 and 2), EX-066 (the boundary)

### PREF-046
**An opportunity's benefit is an advantage toward a goal, never the goal itself. Its trigger can be an action or achieving another goal.**
- Scope: opportunities (the unified pipeline's `could_use` openings)
- Evidence: stated (SRC-58); the two example bullets were the agent's, and the user approved them
- Source: SRC-58 (2026-11-01)
- Quotes (verbatim):
  > An opportunity, generally speaking, has this: if trigger, then benefit, shape. And that's really what defines an opportunity: if the players do something or achieve some intermediate goal, it provides them with a benefit.

  > it provides a benefit that will help them overcome the obstacles that are blocking a goal or otherwise makes the goal easier to achieve.

  > One of the shapes that I definitely think we need to be looking out for is the benefit itself, not the achievement of the goal, right? This is why the treasure map failed. And why the farmer Gill and the mule failed is because it says if trigger, then not a benefit that helps them to achieve later in achieving the goal, but instead just it is a way to get the goal. And while that might be considered like an approach to achieve your goal, it is not this very specific meaning of the term opportunity.

  > Yes this works.
- Meaning:
  - **The benefit** is an obstacle overcome or a goal made easier. "If the party does X, they get the goal" is an approach, not an opportunity. Examples: searching the map's marks to find the treasure (EX-074), paying the mule's price (EX-054).
  - **The trigger** can be an action or achieving an intermediate goal. A goal can trigger an opportunity toward another goal: "If the party gets Warwick's mithril shirt, Dunk says it is magical armor to wear against the dragon."
  - **A plan ends at its advantage, not at the goal.** "If Dunk helps Ingrid give Warwick her sleeping potion, Warwick will stay asleep while they are in his house", not "…Dunk could take the shirt".
  - **A chain splits where it crosses into another goal** (refines [PREF-045](#pref-045) pattern 2). The potion plan serves the shirt goal, and the shirt serves the dragon goal, so they are two opportunities.
- Ambiguity the user accepts: whether the shirt is a goal in its own right or only a means to the dragon is "an ambiguous case" (see EX-036). The two-bullet form holds when the pipeline judges it a goal. Verbatim:
  > There is an interesting discussion here about whether or not getting Warwick's shirt is itself its own goal or only a means to help them in fighting the dragon. But I actually think this is an ambiguous case, and if you assume that Warwick and, wait, and if the pipeline judges Warwick's shirt as being its own goal, then I think these two bullets make total sense.
- Refines [PREF-035](#pref-035)'s "an extra action that can be taken to provide an extra advantage", and supersedes the "generic usefulness" reading of EX-074 for the shirt bullets (see EX-074's 2026-11-01 reinterpretation).
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s facts, reconciliation and writing prompts, where `generic_benefit` now means vague usefulness only (2026-11-01). Pass 8 and 9 classify the shirt's usefulness against the dragon as `generic_benefit` and hide it (pass 9 Session 002, fact_31), which this preference contradicts; pass 10 changes that, but it has not yet been checked against generated output.
- Examples: EX-054, EX-074, EX-040, EX-036

### PREF-047
**Something already held is not an opportunity, because nothing remains to trigger. An action that uses held help can be one.**
- Scope: opportunities, new-assets (held help in the unified pipeline)
- Evidence: the agent proposed this general form and the user confirmed it (SRC-58). It generalizes the user's stated judgments in EX-075 and the pass 7 approval.
- Source: SRC-58 (2026-11-01); SRC-57 for the underlying judgments
- Quotes (verbatim):
  > This is an asset not an opprtunity, they have already acquired it

  > assets are not open matters, so don't (and should not) show up there.

  > Yes that works
- Meaning: in the "if trigger, then benefit" form ([PREF-046](#pref-046)), something the party holds has no trigger left. "If the party has Squints, they have Squints" is the same tautology as "if they get the shirt, they have the shirt". Held help stays in campaign state and can be told as a gain in history. An action that uses held help to gain an advantage is an opportunity: the action is the trigger. The golden's "If you get the potion from Ingrid, it will keep Warwick asleep…" used wine Dunk already held.
- Generalizes the approved direction in [EX-075](examples/pass7-session-001-002-review.md#ex-075-an-acquired-ally-must-read-as-an-asset), whose wording named two cases ("including Squints and the treasure map"). The pass 9 prompt copied those cases ("An acquired recruit or usable map"), which the review flags as overtuned.
- Encoded in: pass 8 to 10 exclude `form: asset` from open headings in code. [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s facts prompt states the general rule, replacing pass 9's case-shaped one (2026-11-01). Not yet checked against generated output.
- Examples: EX-075, EX-048

## Brewing Troubles

### PREF-037
**A Brewing Trouble is an articulated, developing harm from outside the party that the party could affect.**
- Scope: brewing-troubles
- Evidence: both (the user's review table)
- Source: R-03, SRC-26 (2026-10-23T20:26Z–23:15Z)
- Quotes (verbatim):
  > My point about no expectation or ask for help is that this is *not* an unfolding rescue problem, and was trying to find a litmus test for establishing that.

  > my only push back here is that this is existing trouble more than brewing trouble.

  > Right he is actually an opportunity (albiet a disturbing one) for the party, not a danger that the party has to stop

  > something can't be a trouble if the party itself (like dunk) is the source of the trouble
- Unsettled: whether a recurrence of an existing harm counts. Recurring and continuing harms are "temporarily" allowed (2026-10-23T23:15Z).
- Encoded in: Brewing Troubles classification fields, `harm_origin`, and filtering in code.
- Examples: EX-045, EX-046, EX-063

**Established-danger clarification (2026-11-01, SRC-60; EX-045 follow-up):** the adventure/play must establish danger or developing harm absent intervention. A plausible risk inferred from someone’s activity is insufficient, and competition for prospective loot, rewards or other benefits is not itself a trouble. A rescue request, quest acceptance and player action are not prerequisites: established danger the party could affect qualifies without them. Gill’s sons are rejected as an independent rescue trouble because the adventure does not frame them as endangered. This settles that candidate’s earlier “Maybe-” ambiguity without changing the separate provisional allowance for recurring harm. Prompt implementation is deferred until the remaining pass 12 feedback has been discussed.

## New Assets

### PREF-038
**A New Asset is a gain that helps with an open Goal. It has a short name and a separate, short benefit.**
- Scope: new-assets
- Evidence: stated
- Source: SRC-13 (2026-10-20T15:54Z–15:59Z), SRC-36 (2026-10-26T16:04Z–18:56Z)
- Quotes (verbatim):
  > We should include both its name and its benefit, but they should be different properties in the JSON if that makes sense. It's not one big group thing.

  > Can you add something to that rubric about that I, the developer, can later choose which of these things show up in a table recap?

  > a new asset is something that provides help, support, or benefit in achieving one of the open goals, or overcoming one of the open impediments, or capitalizing on a new, on a currently open opportunity

  > every asset must still support at least one currently open matter. Ultimately, this means a goal because every impediment or opportunity will point at a goal as well.
- Filter (user's amended wording, 2026-10-26T18:56Z): exclude assets that did not come from an opportunity and whose "goal support is low or trivial".
- Encoded in: New Assets prompt; required `goal_id`; optional opportunity and impediment IDs; a from-opportunity flag; goal-support rating; the code filter.
- Examples: EX-047, EX-048

## Developments

### PREF-039
**A Development is a notable change in the fiction with lasting consequences. Transient effects, ordinary treasure, and gains or discoveries covered by other matters are excluded.**
- Scope: developments
- Evidence: stated
- Source: SRC-37 (2026-10-26T19:29Z–20:07Z)
- Quotes (verbatim):
  > Developments represent the notable state changes in the state of the fiction that persist beyond the session.  This means changes like 'frank took damage' or 'alice moved down the stairs' or irrelevant because they are not likely to matter after a session ends.

  > Gaining of treasure like gold or non magical items are not significant developments.

  > Q2 - no it should exclude them.  we can pass those into the prompt as well before building Developments

  > - title: reads like a new york times headline, not exclamation points.    This is what is read in a table recap.
- Q2 answered whether Developments should exclude gains and discoveries already covered by New Assets and Revelations.
- Golden: the Session 001 "Last session..." list from pass 5 (EX-057), 2026-10-30.
- Ratings: narrative impact ("how substantially the development changed the fictional situation last session"), lasting consequences, and screen time ("I prefer the time spent at the table").
- Related: past tense and chronological order ([PREF-027](#pref-027)).

## Revelations

### PREF-005
**Revelations are retrospective: they advance an established Mystery, or reverse or reframe an established understanding that either speaks to an open matter or has large narrative impact.**
- Scope: revelations
- Evidence: stated
- Source: SRC-33 (2026-10-25T04:19Z–04:35Z)
- Quotes (verbatim):
  > Roughly speaking this is a retrospective matter that lists gains in knowledge that progress an open mystery from last session, or a reversal/twist of understanding about an open goal, mystery, impediment, obligation or opportunity from last session.

  > Q1, a - no unless the location was a mystery or a reframing (they believed it was in a different place previously,)

  > B, and that applies even when previous matters are included

  (This answered whether Mysteries established this session also count.)
- Details settled in the same thread:
  - Useful knowledge for a Goal alone does not qualify.
  - Matters from this session as well as the previous one are eligible.
  - Both prior and current matters are supplied as inputs, so the model does not have to infer them.
- Encoded in: `st:`/`pt:` revelations, definition and `system.md:73`.
- Examples: EX-008, EX-011

### PREF-002
**Headline text: restrained, no exclamation marks, small words kept, sentence case.**
- Scope: revelations, and also historical matters generally (New Assets, Developments)
- Evidence: stated
- Source: SRC-33 (2026-10-25T18:11Z), SRC-41 (2026-10-27T21:32Z), SRC-44 (2026-10-28T20:26Z)
- Quotes (verbatim):
  > I want the description to read like a new York times newspaper headline. No exclamation marks.

  > …headline style formatting, which is great, but they keep dropping articles and other small words to create that compressed, slightly harder to read headline. I want to keep that same, you know, most of that same compression and most of the formatting and style the same, but just don't drop those words.

  > I think it might be title cased and not sentence cased.
- Encoded in: `pt:` revelations `system.md:80–93` (sentence case, small words kept). **Drift:** `st:` revelations `system.md:80` still says "Use title case".
- Examples: EX-013

### PREF-007
**One point per entry; keep detail that changes how the party could use the knowledge, drop detail that only adds precision.**
- Scope: revelations (origin), also applied to other matters
- Evidence: both
- Source: SRC-03 (2026-10-18T20:03Z, 20:51Z)
- Quotes (verbatim):
  > keep a detail when it changes how the party could use the knowledge, and drop it when it only adds precision.

  > yes the three miles north is only precision and should be cut.  i  know there was a correction about it in the session, but it is still unneeded precision no matter.
- Also out of the text: current state ("tied up in a bag"), how it was learned, wrong guesses, and mystery bookkeeping ("This solves…").
- Encoded in: `st:`/`pt:` revelations `system.md:83` ("Keep details that change the finding's meaning or use … Remove incidental precision, background, acquisition history…").
- Examples: EX-009

### PREF-008
**Table talk is not evidence: player speculation, and a PC correcting another PC from known lore, are not Revelations.**
- Scope: revelations (the speculation rule applies to every matter)
- Evidence: both
- Source: SRC-03 (2026-10-18, Q1: "players' own theories do not" count), SRC-35 (2026-10-26T01:31Z)
- Quote (verbatim):
  > i just dont think a revelation can come from a pc, or from another pc correcting them
- Refinement: a PC *reporting* a real discovery still counts. The speaker alone does not decide eligibility.
- Encoded in: `st:`/`pt:` revelations `system.md:67`, `:86`.
- Examples: EX-006

### PREF-009
**Uncertain claims can qualify, but stay attributed and carry a filterable evidence-strength rating.**
- Scope: revelations
- Evidence: stated
- Source: SRC-33 (2026-10-25T04:30Z)
- Quote (verbatim):
  > A but add a filter able attribute that specified how well established it credible it is
- Encoded in: the `evidentiary_strength` field; `st:` revelations `system.md:81` (preserve attribution for uncertain testimony).
- Examples: EX-010

### PREF-010
**Filter out predictable Revelations.**
- Scope: revelations
- Evidence: stated
- Source: SRC-35 (2026-10-26T01:09Z, 01:11Z)
- Quotes (verbatim):
  > my goal is to be able to filter out very predictable results.  In a way this kind of like measuring the entropy reduction is in a revelation and only capture those that reduce entropy significantly.  This needs to be something that can be well measured by an llm (unlike entropy).

  > i am good with unexpectedness but would like to remove undetermined and add a trivial option.
- Encoded in: the `unexpectedness` field (`trivial`/`low`/`medium`/`high`); standalone publication keeps `medium`+.
- Approaches: [APP-007](approaches.md#app-007)

## Mysteries

### PREF-003
**A Mystery is an established question whose answer is a meaningful revelation in its own right, not an ordinary unknown.**
- Scope: mysteries
- Evidence: both
- Source:
  - user-authored definition file (SRC-34, 2026-10-25T19:42Z; R-06)
  - reactions in SRC-32 and SRC-33
  - the open-ended requirement (SRC-32, 2026-10-25T03:17Z)
- Quotes (verbatim):
  > A **Mystery** is an unresolved question established by the fiction whose answer promises a meaningful narrative revelation and could serve as a worthwhile investigative objective for the player characters.

  > **Ordinary unknowns are not mysteries.** Missing tactical information, unidentified objects, unknown abilities, and routine information gaps do not qualify unless their answers promise a meaningful narrative revelation.

  > Neither feel to me like investigative targets. Yes they are unknowns, but they are not questions the party is existed to find out for its own sake.

  > can you add a filtering attribute for whether the question is open ended, like "why is the king raising an army?" versus close yes/no or how many out how much questions
- From the definition file: player pursuit is not a criterion. A Mystery does not need the characters to have expressed interest.
- Encoded in: `st:`/`pt:` mysteries definition, four dimensions, `question_type`. The filter keeps entries with all four dimensions `medium`+, `open` lifecycle and `open_ended` questions.
- **Tension:** instrumental questions score low narrative payoff, so the treasure question the goldens keep is filtered out (EX-017).
- Examples: EX-002, EX-014, EX-015, EX-016, EX-017, EX-019, EX-020, EX-062

### PREF-013
**A local Mystery becomes obsolete when its episode ends and the party moves on.**
- Scope: mysteries
- Evidence: reaction
- Source: SRC-34 (2026-10-25T23:53Z)
- Quote (verbatim):
  > I was expecting these to be marked obsolete one they left the barrow mound
- Encoded in: `st:`/`pt:` mysteries lifecycle guidance (episode-ending rule).
- Examples: EX-018

## Obligations

### PREF-036
**An Obligation is something a recipient has a claim on: specific, finite, and something they actually care about.**
- Scope: obligations
- Evidence: both
- Source: SRC-10 (2026-10-19T17:53Z), SRC-41 (2026-10-27T21:13Z–21:24Z)
- Quotes (verbatim):
  > The lake thing is not a commitment, it is just phidipaldis acknowledging George's advice. George does not care or have a stake in him using his lane.

  > The field should be type of commitment and some values should for sure include general agreement, which is what happens if somebody, you know, suggests an approach and a player just agrees to the approach. … I want to filter out general agreement.

  > Now, can you add another property called stake, which is how much of a stake the person obligated to whom the obligation is owed has in you fulfilling the specific terms of this oath?
- Encoded in:
  - pt Obligations: `commitment_type` (`general_agreement` filtered out), `stake`, `burden`, `consequence` (`trivial` filtered out), and the outstanding lifecycle.
  - st: the definition requires a finite completion condition.
- Also stated 2026-10-30 (SRC-55), verbatim, about "Promises and debts":
  > this is a section for the party making a Promise or owing a debt, not situations where somebody owes a debt or makes a promise to the party

  A method the party agreed to try toward a goal is an opportunity, not a promise (EX-056).
- Examples: EX-042, EX-043, EX-044, EX-056

### PREF-052
**A promise or debt exists only if not doing it would break faith with someone who has a claim on that specific act. Provisional.**
- Scope: obligations (the unified pipeline's `owe` facts)
- Evidence: the agent proposed the test, drawing on the user's EX-076 wording, and the user agreed to try it (SRC-58)
- Source: SRC-58 (2026-11-01)
- Quote (verbatim):
  > I am fine to try your proposal or breaking faith
- Meaning: agreeing with advice, showing you value someone's opinion, or saying you plan to come back gives nobody a claim. A word like "vow" in a paraphrase of the scene doesn't decide it; what was actually said, and who relies on it, does. This restates [PREF-036](#pref-036)'s "something a recipient has a claim on" as a test that works for any wording. It replaces the pass 9 rule "the word 'vow' alone is not enough", which was aimed at one Ledger's paraphrase. The user's source wording (EX-076): "If the party or Sir Phidipaldi never goes back, he is not breaking an oath or contract".
- Status: on trial. Revisit if it lets through, or hides, commitments the user judges differently.
- Encoded in: [pass 10](../.work-items/unified-matters-pipeline/experiments/session-004/pass-10/README.md)'s facts and writing prompts (2026-11-01). Not yet checked against generated output.
- Examples: EX-042, EX-076, EX-056

### PREF-020
**A promise with no end, such as a promise never to do something, is something that happened, not an open matter.**
- Scope: obligations (and the unified pipeline's promises)
- Evidence: stated
- Source: SRC-10 (2026-10-19T17:50Z), SRC-55 (2026-10-29T21:45Z, 21:50Z)
- Quotes (verbatim):
  > The problem with recurring terms or negative terms like 'I will not reveal your presence to king hogboon" is they and never be completed.

  > a promise not to do something is actually a promise and could be treated as a development in the past tense, but is never an open matter, so we just need a property that can filter on, you know, has definite end or something.
- Related (verbatim, 2026-10-29T21:45Z):
  > I think you can treat money owed to the party as an asset if there's nothing that they need to do to get it, and an opportunity if there's something they need to do to be able to collect.

## Unified Review Decisions (2026-10-31)

### PREF-040
**Supported options do not require an explicit proposal.**
- Scope: opportunities and useful assets (`could_use`).
- Evidence: stated approval of a hypothetical comparison, SRC-57.
- Quote (verbatim, response 1):
  > I prefer production (i approve your recommendation)
- Meaning: allow established access/capability and advantage to support an option without someone proposing it aloud. Straightforward capability-to-need matching is permitted. Do not invent acceptance, negotiated terms or cooperation; EX-055 remains rejected.
- Encoded in: production guidance and unified pass 7 `action_supported` extraction/classification/selection. Implemented 2026-10-31 at the user's request; deterministic checks passed, real output quality not yet assessed.
- Examples: [EX-065](examples/opportunities.md#ex-065-a-supported-opening-need-not-have-been-proposed-aloud), [EX-080](examples/opportunities.md#ex-080-a-paid-offer-of-help-hidden-because-it-didnt-name-the-goal).
- Applied 2026-11-01 (SRC-58): an actual offer of help serves any shown goal that what it brings plainly serves, even when the offer didn't name that goal; its conditions are its cost. The user, verbatim: "the drop ded ned opportunity, which to me is the same as hilda." This matching is the general rule behind the case-shaped "a paid ally's actual offer… can be enabling" that pass 10 removed (EX-080).

### PREF-041
**Keep distinct resources as separate facts; deduplicate only the same resource.**
- Scope: cross-matter, opportunities, new-assets.
- Evidence: stated, SRC-57.
- Quote (verbatim, response 2):
  > I prefer keeping these as seperate items, not combined (so closer to unfiied, but with changes you may recommend to increase the likelyhood of this. (i approve your recommendation)
- Meaning: the chart and boat passage in the example remain distinct. Shared home/helped threads do not establish equivalence. Eligibility is independent; separate storage does not require publishing every resource.
- Encoded in: unified pass 7 separate-resource prompting, validated resource-subject references and conservative selected-home deduplication. Implemented and directly checked 2026-10-31; no Session rerun.
- Examples: [EX-066](examples/cross-matter.md#ex-066-distinct-resources-must-survive-shared-thread-deduplication).

### PREF-042
**Separate immediate confrontation from lasting impediments.**
- Scope: goal-impediments, present-matters.
- Evidence: stated approval, SRC-57.
- Quote (verbatim, response 3):
  > I prefer production (i approve your recommendation)
- Meaning: a scene-local guard confrontation appears as Immediate danger, not also as a cumulative impediment. A distinct continuing obstruction can remain a fact. Published impediments require a live relevant pursuit.
- Encoded in: production boundary and unified pass 7 explicit lasting-scope/live-target selection plus immediate-danger coverage for obstacles. Implemented and directly checked 2026-10-31; LLM behavior not yet assessed.
- Examples: [EX-067](examples/cross-matter.md#ex-067-a-scene-local-confrontation-belongs-in-immediate-danger).

### PREF-043
**Intentional table revelations count without a separate in-character discovery.**
- Scope: mysteries, learned beats, revelations.
- Evidence: stated rejection of the agent's recommendation, SRC-57.
- Quote (verbatim, response 4):
  > I prefer the unified approach - information revealed at the table, if not an accidental slip, is established fact in the fiction and can be included.  (not your recomendation)
- Meaning: an intentional authoritative disclosure can settle an unknown despite no character witness. Accidental slips are excluded; attributed claims remain claims. Do not invent an in-character information-transfer event.
- Definition difference: supersedes production's character-only resolution boundary as the desired unified behavior. Preserve that older rule as historical/current production behavior, not a rule to port. This supplements PREF-003; Mystery qualification thresholds are unchanged.
- Encoded in: unified behavior preferred; no new production-style knowledge restriction is authorized.
- Examples: [EX-068](examples/mysteries.md#ex-068-an-intentional-table-revelation-can-settle-an-unknown).

### PREF-044
**Investigate the low-impact/high-lasting historical cutoff before changing it.**
- Scope: developments, Last session selection.
- Evidence: stated deferral and investigation request, SRC-57.
- Quote (verbatim, response 5):
  > I think we need to investigate this and see what impact it would have on our four test sessions.   Please make this investigation a new work items (allow low impact developments with high lasting consequences) and we will do an investigation later.   make no change to the unified pipeline for now.
- Meaning: compare impact across Brandonsford Sessions 001–004 later. No new keep/drop preference or cutoff is approved. Retain the current rule and existing goldens meanwhile. Follow-up requirement (SRC-57): run with and without the narrow change, show differences, and provide a likelihood for each difference that it came from the change. Full [handoff](../.work-items/allow-low-impact-developments-high-lasting-consequences/intent.md) saved; investigation remains deferred.
- Encoded in: current unified selection unchanged; investigation registered in [the work-item index](../WORK-ITEMS.md).
- Examples: [EX-069](examples/developments.md#ex-069-investigate-low-impact-changes-with-high-lasting-consequences).

### Pass 7 Review Clarifications (SRC-57)

Actual Session 001–002 judgments and their scope are in [EX-070–EX-078](examples/pass7-session-001-002-review.md). PREF-033: dropped/expired duel is excluded; improve goal priority, but the exact sorting rule and minor mule boundary remain unresolved. PREF-035/PREF-040: supported implicit openings remain allowed; direct goal pursuit and generic armor benefits are not additional openings. PREF-041: Hilda, sword and potion plan paraphrases are duplicates, while genuinely distinct resources stay separate. PREF-036: an intention to return and hire is no debt; no requirement that every valid personal promise be a legal contract is established. Acquired Squints is an asset (already correctly classified); grouping its presentation is an agent proposal. The current tier should convey the established immediate direction without inventing Dirk's agreement. No behavior change has been made.

### Approved Pass 7 Review Direction (SRC-57)

The user approved EX-070–EX-078 recommendations before implementation. [Exact corrections](examples/pass7-session-001-002-review.md#approved-implementation-direction-recorded-before-behavior-changes) supersede the preceding unresolved/proposed labels: the mule remains incidental absent meaningful new stakes; goal sorting puts adventure first; same offers/plans are reconciled while distinct resources survive; agreements do not become debts without evidence. Assets are **not open matters** and must not appear in open What could help, including Squints and the treasure map; preserve them in state and appropriate historical gains. This supersedes the agent's proposed Assets/Opportunities grouping under that open heading. The immediate plan is optional, only when established. No explicit withdrawal of the duel exists or is required: scene-local nonacceptance and subsequently elapsed fictional time matter.

### Pass 8 Feedback Clarifications (2026-11-01, SRC-57)

PREF-036 is reaffirmed by the [EX-042 recurrence](examples/obligations.md#ex-042-recurrence-pass-8-and-renewed-user-judgment-2026-11-01): acknowledging advice and showing that the speaker values it does not establish a promise owed to its giver. Do not invent a stake in a particular method from concern for the overall outcome. The user calls the lance an edge case and discourages unnatural acts to fit it; prefer the existing general distinction over special machinery.

[EX-079](examples/developments.md#ex-079-dunks-visit-to-farmer-gill-disappears-as-a-historical-event) establishes that Dunk's visit to Gill deserves historical representation even though most incidental detail can be omitted. It does not make the mule a displayed Goal, establish a one-bullet-per-character rule, or approve a new historical cutoff.

Deferred low-stake filtering (2026-11-01, SRC-57): the user explicitly wants to explore excluding low-stakes commitments later, after general output quality is satisfactory. [Registered work item](../.work-items/filter-low-stakes-commitments/); [evidence and timing](examples/obligations.md). This supplements PREF-036 as an approved investigation, not an approved inclusion-threshold change.

Approved encounter coverage (2026-11-01, SRC-57/EX-079): the user authorized the general remedy and fresh Sessions 001–002. Noteworthy encounters can have historical value independently of enduring consequences or open-matter significance. Preserve scene context when evidence is split across threads; avoid same-event restatements and quotas. Pass 9 implements this policy via an additional encounter candidate channel in the existing historical call. The earlier impact/lasting conjunction remains only for thread/standalone candidates; do not describe the overall historical policy as unchanged. Deferred low-stakes and low-impact/high-lasting investigations remain deferred.

EX-079 positive inclusion confirmed (2026-11-01, SRC-57): the user explicitly asked to preserve the presence of Dunk/Gill as a Session 001 Development as a learning. Keep this as a good inclusion example for encounter-level history; the mule can remain excluded from Goals. This is not approval of every word or all pass 9 outputs.

## Pass 11 User Judgments (2026-11-01, SRC-59)

### PREF-053
**Judge a goal's significance by what achieving its actual end would change, not by its proposed method or the drama surrounding it.**
- Scope: goals and dependent impediments.
- Evidence: stated, SRC-59, EX-081.
- Quote (verbatim):
  > the goal here is not to have a duel, it is to restore his honor.  also i think this is too minor and not enough narrative impact (I mean that achieving the goal does not provide much narrative impact).
- The user also rejects nonacceptance of the duel as an obstacle to that broader end and wants the minor goal filtered from the Summary. This does not require inventing honor motives in other cases, ending every underlying goal when one method expires, or discarding state/history evidence of the encounter.
- Encoded in: not implemented. Existing significance/incidental filtering is available, but pass 11 rates this pursuit side. Reusing that classification or adding an impact field remains a proposal.

### PREF-054
**Adventure-level goals should not be excluded by the low-impact filter.**
- Scope: adventure-level goals; stated in response to the missing treasure Mystery (RC-049), with the exact question-selection scope still to be settled.
- Evidence: stated, SRC-59, EX-017 follow-up.
- Quote (verbatim):
  > this is more bothersome for me, because adventrure level goals should be excluded from the low impact filter
- Current behavior: the treasure Goal is already shown as adventure; its question is hidden by low investigative depth and narrative payoff, rather than a goal-impact cutoff. The feedback calls for protecting adventure-level content from overfiltering. A new path for objective-defining adventure questions, which thresholds to exempt, and its boundary against ordinary unknowns are proposed design choices, not approved mechanisms. It does not authorize publishing all questions merely because their thread contains an adventure goal.
- Encoded in: no behavior change.

### Dated Clarifications to Existing Preferences

- **PREF-033 / PREF-051:** EX-081 clarifies end versus proposed method and the impact of attaining that end. The user still requests the stale pursuit be fixed. Reconcile a method's expiry separately from whether its underlying end remains wanted and significant. Do not preserve the duel as the end or silently infer an unspoken end in other cases.
- **PREF-034:** an obstacle must actually constrain the supported end; a refused method does not automatically block it (EX-081). Hidden insignificant pursuits must not leave published dependent impediments without another live target.
- **PREF-050:** the reporting hierarchy detail is again rejected as unimportant to future play, even in Where you are (EX-078 recurrence). Preserve the meaningful current intention without its unrelated detail. This does not revoke the approved encounter-history exception (EX-079).
- **PREF-027:** chronological history remains wanted; the user approves addressing RC-022. Anchoring narrated changes and sorting by their actual source chronology is a proposed mechanism.
- **PREF-028 / PREF-046:** the user wants RC-037 wording addressed, but accepts EX-074's specific “it could help against the dragon” benefit. Do not make explicit armor-mechanism wording mandatory for that accepted case. This leaves the broader requirement for a useful advantage intact; any revised universal sentence-count rule is still a proposal.
- **PREF-003:** the Session 001 dragon-origin omission (SE-005) is acceptable “for now”; the Session 002 loss (SE-014) is worth fixing. These are distinct Session judgments, not a global include/exclude rule. PREF-054 records the related adventure-level filtering concern without silently resolving its wider Mystery-definition implications.
- **PREF-005 / PREF-039:** map marking is not a standalone Revelation but is acceptable as a Development (RC-067). Old Revelation eligibility must not automatically constrain unified history.
- **EX-071 ordering:** the user asks whether ordering can be deterministic. It already is; choosing a revised narrative priority classification or tie-break remains a proposal.

Exact outputs, user quotes and current behavior are preserved in [the pass 11 review](examples/pass11-session-001-002-review.md). No prompts, code, generated outputs or derived guide changed from these judgments.

**Pass 12 approval and implementation (2026-11-01, SRC-59):** “implement then run pass 12” approves the seven generic proposals, settling the proposed adventure-objective question path and priority/event-anchor mechanisms for this experiment. PREF-054 now includes grounded, open-ended, investigable questions defining a shown adventure goal, without requiring independent depth/payoff; it does not exempt ordinary gaps. PREF-028 permits an essential second short sentence, and contextual benefits need no forced mechanism explanation. PREF-053 uses existing significance/incidental filtering rather than a new completion-impact threshold. See the pass 12 README; mechanics are checked, generation is underway, quality is not yet judged.


**PREF-033 / EX-071 priority clarification (2026-11-01, SRC-60):** the user approves putting the adventure currently driving the party’s choices first among adventure goals. In pass 12 Session 002 this is the dragon hunt, ahead of treasure; no named-goal exception is intended. Improve evidence-based priority classification feeding deterministic sorting rather than ordering by isolated immediate actionability.


**PREF-035 / PREF-046 direct-pursuit clarification (2026-11-01, SRC-60, EX-074):** the user confirms that having a trigger does not suffice for an opportunity. Its benefit must provide an advantage that makes attaining a goal easier, rather than simply solving that same goal. The map-checking opportunity should be removed; retain useful established immediate plans only in their appropriate section. This does not prohibit one goal’s achievement providing an advantage toward another goal.
