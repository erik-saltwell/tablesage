# Preferences

What the user wants from the Session Summary, the Table Recap and the unified Matters pipeline. Each entry is the **current state** of one rule: every later clarification, refinement and pass decision is folded into it, so a reader never has to assemble a rule from several places.

Entries are grouped by the Summary heading they govern, in Summary order, after the rules that apply across the pipeline or across the whole Summary. The heading map is in the [README](README.md#summary-headings).

Each entry has:
- **Status:** `firm`, `provisional` (kept, but the user asked to watch it), `on trial` (being tried), or `superseded` (kept as history, with a pointer).
- **Rule:** what to do now, with its boundaries. A boundary says what the rule does *not* require.
- **User's words:** verbatim quotes. Dictation slips are kept, with a [gloss] where needed.
- **Evidence:** the examples (`EX-###`) and allowances (`ALW-###`) behind it.
- **History:** one dated line per change in meaning. Older wording that examples were judged under is kept here.
- **Source:** the `SRC-##` conversations in [sources.md](sources.md).

Where a rule and a prompt disagree, the prompt is current behavior and the rule is what the user wants.

## Pipeline and Process

### PREF-014
**The model classifies; code decides what to keep.**
- Status: firm
- Rule:
  - Prompts ask the model to classify each candidate on defined dimensions. A deterministic filter in code decides what is shown, and records what it drops so the drops can be reviewed.
  - The model lists every candidate with its ratings, including low-rated ones. It must not leave candidates out because they seem unimportant.
  - Defining what counts as a fact kind, or excluding plain colour and routine, is a definition, not a keep/drop decision.
- User's words:
  > The approach i want to keep is that the llm does not make exlude/keep decisions.  it classifies on a number of dimensions, and i run a deterministic filtering pass on what comes back from the llm

  > I always add the filtering after i run this workflow so that i can see the unflitered results when i run validate.  this is how i decide what to filter.
- Evidence: EX-001, EX-007, EX-017, EX-020; [APP-001](approaches.md#app-001), [APP-011](approaches.md#app-011)
- History: 2026-11-01 (SRC-58), applied to history: the model lists every beat that touches no thread as a standalone history candidate, and code drops the `low` ones with a record. The user: "Agreed".
- Source: SRC-26, SRC-58

### PREF-012
**Prompt examples are fictional, never echo the test Sessions, and teach general distinctions.**
- Status: firm
- Rule:
  - An example in a prompt comes from an unrelated fictional setting. It must not reuse a test Session's names, items, situations or expected answers, even in disguise.
  - A prompt rule states a distinction that applies generally. A rule that exists only to fix one remembered case is overtuned, even when fictionalized. When a case exposes a problem, look for the general pattern behind it (as PREF-045 to PREF-053 did) before writing a rule.
- User's words:
  > We need to use an example not from our sessions, so we can test correctly

  > I actually want the prompt for now to not mention people having other problems, that is too close to the session text

  > Is there something more generic and Less situation specific that would work?

  On the general patterns PREF-045 to PREF-052 (2026-11-01):
  > update the learnings to include these new patterns, which I love and I think really get to the underlying issues we're talking about.
- Why: an example built from test-session text lets the prompt memorize the answer, so a test run no longer shows whether the rule generalizes. A case-specific fix recorded in the learnings tends to come back as a disguised copy in the prompts ([APP-034](approaches.md#app-034)).
- Evidence: EX-014, EX-044, EX-042 (2026-11-01 recurrence: "I wouldn't do any unnatural acts to fit it"), EX-079 (general-fix request); [APP-013](approaches.md#app-013)
- Source: SRC-32, SRC-10, SRC-57, SRC-58

### PREF-018
**Redesigns are built side by side and replace existing artifacts only once their quality is proven.**
- Status: firm
- User's words:
  > I just want to be able to compare side by side because the existing artifacts are great in many ways and outside of the duplicate issue I want to make sure that we retain all the goodness we had prior.
- Evidence: [APP-034](approaches.md#app-034)
- Source: SRC-55

### PREF-015
**The Summary answers three questions: what happened, where are we, and what's ahead. Building it takes four steps: decide what is true, what to keep, where it goes, and how to phrase it.**
- Status: firm. This is the basis of the unified pipeline.
- Rule:
  - "Last session..." tells what happened; "Where you are" and "Immediate danger" tell where the party is; the open headings tell what's ahead.
  - Overlap between what happened and what's ahead is legitimate but costs the reader (PREF-004).
- User's words:
  > there are good reasons to keep in both Developments and at least one Open Matters.  So in a way i am saying that it is both a problem and not a problem

  > - previous matters: what happened?  (btw i am unconvinced that new assets and revelations are earning their keep beyond developments.  I am not looking to kill them, just know i am on the fence.   particularly new assets)
  > - current matters: Where are we?  Current situation and current (?) danger
  > - open matters: What's ahead? Goals, impediments, opportunities, mysteries, and obligations (and of all of these, i am on the fence about obligations)

  > Is it possible that there are four steps in this unified flow? One, determine what's true, which is the creation of threads and facts. Two, determine what to keep. Three, determine where it goes. And four, determine how to phrase it.
- Evidence: EX-003, EX-025; [APP-034](approaches.md#app-034)
- Source: SRC-55

## Across the Summary

### PREF-004
**Each heading carries only its own angle; the same content is not restated under several headings.**
- Status: firm
- Rule:
  - Sharing a subject across headings is fine when each bullet adds something the others lack: an event and a fact, a gain and a price, a want and an obstacle (EX-025, EX-026).
  - Restating a whole item under another heading is the defect: an open bargain told as event, goal and opportunity (EX-003, EX-024), one live threat told as danger, obstacle and trouble (EX-021), one promise told as event and two debts (EX-022), learned knowledge repeated as an obstacle (EX-023).
  - Within one heading, two bullets that are the same item are duplicates (PREF-045 for openings).
- User's words:
  > some kind of developments seem to show up in many post session matters, and they don't seem to add any extra information. They are just things that could apply in multiple matters, so the llm phrases it in ways appropriate for different matters and they end up all over the place.
- Evidence: EX-003, EX-021 to EX-026, EX-073
- Source: SRC-51, SRC-53, SRC-01

### PREF-017
**The stopping situation may repeat items from other headings.**
- Status: firm
- Rule: "Where you are" and "Immediate danger" may mention something that also appears under "Last session..." or an open heading. A scene-local confrontation still belongs in "Immediate danger" alone rather than also as a lasting obstacle (PREF-042).
- User's words:
  > (b)  I am ok if present matters duplicates something in previous/open matters
- Evidence: EX-021
- Source: SRC-42

### PREF-041
**Keep distinct resources as separate facts; merge only the same resource.**
- Status: firm
- Rule:
  - Two resources that serve the same goal stay separate when they are different things or different ways forward: a chart and passage on a boat; hiring an ally and retrieving a weapon.
  - Sharing a thread or a helped goal does not make two facts the same resource.
  - Paraphrases of the same offer or plan are one fact (PREF-045). Each separate resource is judged for publication on its own; being stored does not require it to be shown.
- User's words:
  > I prefer keeping these as seperate items, not combined (so closer to unfiied, but with changes you may recommend to increase the likelyhood of this. (i approve your recommendation)
- Evidence: EX-066, EX-073
- Source: SRC-57

### PREF-050
**Keep a detail only if the players would miss it next Session, or it would change what they do later.**
- Status: firm
- Rule:
  - Cut a secondary event that only adds what else happened, and a description that only says what someone or something is like.
  - The test applies to every heading, so a detail cut from one heading must not reappear in another. A reporting hierarchy ("Trout has told Dirk he will report to Squints") fails it in "Last session..." and in "Where you are" alike.
  - It does not override wanted historical coverage of a noteworthy encounter (PREF-039).
  - It generalizes PREF-007's precision rule beyond knowledge.
- User's words:
  > Yes, I like this. Would the players miss it or would it change their behavior in the future? Kind of a rule.

  > honestly this bit about the reporting hierarchy feels like it should be excluded based on narrative impact guidance.   This fact is not important, and will not change future calls as i understand it
- Evidence: EX-078 (and its pass 11 recurrence), EX-047, EX-059, EX-063
- History: proposed by the agent and approved by the user 2026-11-01 (SRC-58); reaffirmed for "Where you are" 2026-11-01 (SRC-59).
- Source: SRC-58, SRC-59

### PREF-007
**One point per bullet. Keep detail that changes how the party could use something; drop detail that only adds precision.**
- Status: firm
- Rule: leave out current state ("tied up in a bag"), how something was learned, wrong guesses, and bookkeeping ("This solves…"). A distance, amount or count stays only if it changes what the party could do.
- User's words:
  > keep a detail when it changes how the party could use the knowledge, and drop it when it only adds precision.

  > yes the three miles north is only precision and should be cut.  i  know there was a correction about it in the session, but it is still unneeded precision no matter.
- Evidence: EX-009, EX-059
- Source: SRC-03

### PREF-049
**Name a person plainly. A short recognition cue at first mention is optional; never stack labels or add a profile.**
- Status: provisional
- Rule:
  - Name the person. A new or rarely mentioned person may get one short role worked naturally into the sentence ("Quinn, who owns the Golden Egg, …").
  - At a person's first mention in the current Summary, a brief descriptor is acceptable even for a familiar character. It is optional: neither its presence nor its absence is a failure.
  - Never stack two identifying labels in one sentence ("Golden Egg owner Quinn … rival tavern keeper Bentley"). Never add a profile of traits such as weapons, looks or temperament (EX-047). Never repeat an introduction already given in this Summary.
- User's words:
  > Do you have a recommendation here? I'm having a hard time making up my mind.

  > It does. I think that we can keep this, but I would note that we should be on the lookout for if in future runs I give feedback about it in case the cost of the extra complexity and length of the summary turns out to be too high a cost to pay for the benefit. And if it turns out that I believe that just hearing the character's name again is enough of a recognition cue.

  > Ooh, I don't know how I feel here. I think maybe if it's the first time we mention Ned in the summary, then it is fine to add that little aside.
- Watch: if feedback shows the extra length costs more than it helps, or that hearing the name again is enough of a cue, revisit in favour of bare names.
- Evidence: EX-078, EX-057, EX-047, EX-080; [ALW-001](allowances.md#alw-001)
- History: 2026-11-01 (SRC-58), agent recommendation approved: familiar names bare, one role only for new people. Later on 2026-11-01 (SRC-60), the user tentatively accepted a first-mention descriptor even for a familiar character, which relaxes "familiar names go bare".
- Source: SRC-58, SRC-60

### PREF-026
**Plain, sayable wording: actor and action early, attribution first, small words kept.**
- Status: firm
- Rule:
  - Make it clear in the first few words who did, believes, offers or owes something. Put attribution ("X says") at the front, not the end.
  - Keep articles, "is/are/was" and prepositions; a headline must not sound telegraphic when read aloud after its heading (PREF-002).
  - Avoid three or more stacked clauses in one sentence.
  - A prompt's own examples must follow the same rules.
- User's words:
  > I want each bullet to be easier to understand on the first reading and easier to say aloud.

  > - **Put the actor and action early.** Make it immediately clear who did, believes, offers, or owes something.

  > I generally like the phraising and structure used. It is just about the dropping of words
- Evidence: EX-033, EX-034
- Source: SRC-46, SRC-38, SRC-39

### PREF-002
**Event headlines are restrained: no exclamation marks, small words kept, sentence case.**
- Status: firm (originally for Revelations; applies to every headline in "Last session...")
- Rule: write like a restrained newspaper headline without its compression. No exclamation marks; keep the small words (PREF-026); sentence case (PREF-024).
- User's words:
  > I want the description to read like a new York times newspaper headline. No exclamation marks.

  > …headline style formatting, which is great, but they keep dropping articles and other small words to create that compressed, slightly harder to read headline. I want to keep that same, you know, most of that same compression and most of the formatting and style the same, but just don't drop those words.

  > I think it might be title cased and not sentence cased.
- Evidence: EX-013, EX-031, EX-033
- Source: SRC-33, SRC-41, SRC-44

### PREF-024
**Sentence case everywhere, with headings that sound natural when spoken.**
- Status: firm
- Rule: capitalize only the first word and proper nouns, in headings and bullets alike.
- User's words:
  > * "Previously" --> "Last Session..."
  > Otherwise i like all of these.

  > No please use the sentence casing
- History: the heading set approved on 2026-10-28 was "Last session..., You learned, You gained, Your goals, Standing in your way, What could help, Still unanswered, Promises and debts, Meanwhile, As we return, The danger right now." The unified pipeline later dropped "You learned" and "You gained" and renamed the last two "Where you are" and "Immediate danger".
- Evidence: EX-031
- Source: SRC-44

### PREF-025
**Child bullets read naturally after their heading.**
- Status: firm
- Rule: a bullet must not repeat or awkwardly continue its heading.
- User's words:
  > we need to update children bullet lists so they are all phrased to sound natural when read after a heading.  So the heading "You learned"   with a sub bullet that starts with "You learned that"   because that sounds wierd when read
- Source: SRC-44

### PREF-023
**The Session Summary says "the party"; only the spoken Table Recap says "you".**
- Status: firm
- Rule: when something concerns all the attending characters, the Summary says "the party". The Table Recap reframes to "you".
- Evidence: EX-034
- Source: SRC-44, SRC-45

### PREF-021
**Short bullets the GM can paraphrase, never box text. Still-open matters stay in every Summary while they remain open.**
- Status: firm
- Rule:
  - Every section is a list of short bullets, easy to paraphrase or read aloud.
  - An otherwise eligible open matter remains in each Session's Summary for as long as it is open. Unchanged wording from the previous Session is acceptable; do not omit it or reword it cosmetically to avoid repetition.
  - This does not excuse stale or resolved matters, duplication within one Summary, or candidates that are ineligible for other reasons.
- User's words:
  > Box text is universally reviled because read text SOUNDS horrible to listen to - like listenting to someone read a speech while looking down at the text.  players tune out and lose attention. This is why i want the text to be bullet lists - easier to paraphrase and shorter if read.  not the dreaded 'box text'

  > I want to leave the last session content as bullets because otherwise it just becomes a big wall of text that nobody is good at reading.

  > No I agree that as long as it remains open, it should continue to be here.
- Evidence: EX-027
- History: on 2026-10-28 (SRC-44) the user filed a work item against the same lines being read every week (EX-027); that item was closed unimplemented the same day. On 2026-11-01 (SRC-60) the user reversed it for still-open matters.
- Source: SRC-44, SRC-45, SRC-60

### PREF-029
**The Summary's header identifies the Session: campaign name, Session date and Session cue.**
- Status: firm
- User's words:
  > Can you pass in the campagin name to the j2 template, and change "Last time:" to "Prevously on <campaign-name>:"

  > - Session Date - used in header / title
  > - session Cue - I think we generated this previously it is the most memorable scene cue if i remember  I also want to put this in the Header
- History: the "Previously" heading became "Last session..." (PREF-024).
- Source: SRC-39, SRC-55

### PREF-008
**Table talk is not evidence.**
- Status: firm
- Rule: player speculation, and a character correcting another character from lore they already held, establish nothing new. A character *reporting* a real discovery still counts: the speaker alone does not decide it.
- User's words:
  > i just dont think a revelation can come from a pc, or from another pc correcting them
- Evidence: EX-006
- Source: SRC-03, SRC-35

### PREF-009
**Uncertain claims can be used, but stay attributed and hedged.**
- Status: firm
- Rule: keep the source and the hedge of an uncertain claim ("Father William says…", "supposed to"). When accounts conflict about something the party relies on, keep both claims and credit each (EX-010). An evidence-strength rating lets code filter weak claims.
- User's words:
  > A but add a filter able attribute that specified how well established it credible it is
- Evidence: EX-010, EX-048, EX-050
- Source: SRC-33

### PREF-043
**Information intentionally revealed at the table is established fact, even without an in-character witness.**
- Status: firm
- Rule: an intentional, authoritative disclosure to the players can settle an unknown or count as learned, without a separate in-character discovery. Accidental slips are excluded, and attributed claims stay claims. Do not invent an event in which a character learns it.
- User's words:
  > I prefer the unified approach - information revealed at the table, if not an accidental slip, is established fact in the fiction and can be included.  (not your recomendation)
- Evidence: EX-068
- History: this rejects production's character-only boundary, which is kept as production behavior, not a rule to port.
- Source: SRC-57

## Last session...

### PREF-039
**"Last session..." tells notable changes with lasting consequences, and noteworthy encounters.**
- Status: firm
- Rule:
  - Tell notable changes in the fiction that persist beyond the Session. Leave out transient effects (damage, movement) and routine gains of gold or non-magical items.
  - A noteworthy encounter deserves an event of its own even when its consequences are small and its incidental interest (such as a purchase) is not a goal. Hospitality, an established contact or a significant exchange of information can make it noteworthy. Preserve the encounter's context when its evidence is spread across threads. Do not force one bullet per scene or character, and do not repeat an event already told.
  - Historical value does not depend on Revelation eligibility: learning a useful location can be an event (EX-011 follow-up) even though it is not a Revelation.
  - Whether to publish low-impact changes with high lasting consequences is deferred (PREF-044).
- User's words:
  > Developments represent the notable state changes in the state of the fiction that persist beyond the session.  This means changes like 'frank took damage' or 'alice moved down the stairs' or irrelevant because they are not likely to matter after a session ends.

  > Gaining of treasure like gold or non magical items are not significant developments.

  > we lost any mention of dunk and farmer gill. Most of that is fine, but seems to deserve a development at least.

  > agree this is not a revelation, but ok as a developments

  > Yes, I think it is a fine item to put into the last session or development section, although I think its omission is a relatively minor issue.
- Severity: omitting a suitable encounter, such as an unaccepted challenge, was judged a relatively minor issue (SRC-60).
- Evidence: EX-057 (Session 001 golden), EX-079, EX-069, EX-011; [ALW-005](allowances.md#alw-005), [ALW-006](allowances.md#alw-006)
- History: originally (2026-10-26) Developments also excluded gains and discoveries covered by New Assets and Revelations; in the unified pipeline those are told here as events. 2026-11-01 (SRC-57): the user approved the general encounter-coverage remedy after EX-079.
- Source: SRC-37, SRC-57, SRC-59, SRC-60

### PREF-027
**"Last session..." is in the past tense and in the order things happened.**
- Status: firm
- Rule: sort events by when they happened in play, not by thread or importance.
- User's words:
  > can you update the developments matter so that it is generated in the past tense?

  > add A directive for the developments prompt that tells the agent to sort them in the chronological order they happened in the game session.

  > yes we should make this change
- History: reaffirmed 2026-11-01 (SRC-59) when pass 11's Session 002 history began "Father William marked the witch's home and the Barrow Mound on the party's map." and only third told the earlier "Trout and Dr. Uriah caught Naggeneen the Clurichen, who had been stealing Quinn's alcohol, in the Golden Egg's basement."
- Source: SRC-39, SRC-38, SRC-59

### PREF-048
**"Last session..." names the event; amounts and conditions belong to the open bullet. A minor issue.**
- Status: firm, minor
- Rule: when a history bullet and an open bullet share a deal, history tells that it happened ("Eric the Reeve offered a bounty for the dragon") and the open bullet carries the amount, terms and what remains. A fee or price is still acceptable in history when no open bullet carries it (EX-080).
- User's words, choosing "history should name the event ('offered a bounty') and leave specifics like amounts and conditions to the open bullet":
  > B - It was a small lapse; I did not flag, but this is also a relatively smaller issue compared to the other things we have discussed so far.
- Note: the EX-057 golden's "Quinn promised Sir Phidipaldi 100 gold…" beside the goal's "collect his promised 100 gold" is such a lapse, which the user did not flag. EX-057 remains the golden.
- Evidence: EX-057
- Source: SRC-58

### PREF-038
**A gain is told once, as a gain: what the party now has, plus at most the property that makes it useful. Held assets are not open matters.**
- Status: firm
- Rule:
  - Tell an acquisition in "Last session..." as a short gain ("Squints has signed on with the party"), not a profile of the person or thing (EX-047). Keep the one property that makes it useful and its uncertainty ("supposed to make almost anything drunk").
  - Held assets stay in campaign state. They never appear under an open heading (PREF-047).
  - A favour or payment owed to the party is an asset if nothing is needed to collect it, and an opening if action is needed (PREF-020).
  - Routine cash is not a notable gain (PREF-039).
- User's words:
  > We should include both its name and its benefit, but they should be different properties in the JSON if that makes sense. It's not one big group thing.

  > a new asset is something that provides help, support, or benefit in achieving one of the open goals, or overcoming one of the open impediments, or capitalizing on a new, on a currently open opportunity

  > assets are not open matters, so don't (and should not) show up there.
- Evidence: EX-047, EX-048, EX-075
- History: New Assets was its own matter (2026-10-20, rebuilt 2026-10-26), requiring a link to an open goal and filtering weak assets not won from an opportunity. The user was "on the fence" about it (PREF-015); the unified pipeline folded it into history and campaign state.
- Source: SRC-13, SRC-36, SRC-57

### PREF-044
**Investigate the low-impact, high-lasting history cutoff before changing it.**
- Status: firm (deferred decision)
- Rule: history currently requires both narrative impact and lasting consequences to be medium or high. Keep that rule until the registered investigation compares Brandonsford Sessions 001–004 with and without the change, showing each difference and how likely it is to come from the change.
- User's words:
  > I think we need to investigate this and see what impact it would have on our four test sessions.   Please make this investigation a new work items (allow low impact developments with high lasting consequences) and we will do an investigation later.   make no change to the unified pipeline for now.

  > My goal is to do a run with the change and without and show me the differences, and for each difference show me a likellihood the difference came from the change.
- Evidence: EX-069; [work item](../.work-items/allow-low-impact-developments-high-lasting-consequences/intent.md)
- Source: SRC-57

### PREF-005
**Superseded: Revelations as a separate retrospective matter.**
- Status: superseded by the unified pipeline. There is no Revelations heading: what was learned is told in "Last session...", and forward-looking knowledge appears under the open heading of its fact.
- Former rule (2026-10-25): a Revelation advanced an established Mystery, or reversed or reframed an established understanding that spoke to an open matter or had large narrative impact. Useful knowledge for a Goal alone did not qualify.
- User's words:
  > Roughly speaking this is a retrospective matter that lists gains in knowledge that progress an open mystery from last session, or a reversal/twist of understanding about an open goal, mystery, impediment, obligation or opportunity from last session.

  > Q1, a - no unless the location was a mystery or a reframing (they believed it was in a different place previously,)
- What still applies: a finding must reduce an uncertainty rather than restate a question's setup (EX-001, EX-005, EX-007), and the evidence, not the writer, must connect a clue to its question (EX-004). Old Revelation eligibility does not limit unified history (PREF-039).
- Evidence: EX-001, EX-004 to EX-013
- Source: SRC-33

### PREF-010
**Superseded: filter out predictable Revelations.**
- Status: superseded with PREF-005. Kept because the `unexpectedness` rating was its implementation.
- User's words:
  > my goal is to be able to filter out very predictable results.  In a way this kind of like measuring the entropy reduction is in a revelation and only capture those that reduce entropy significantly.  This needs to be something that can be well measured by an llm (unlike entropy).
- Evidence: [APP-007](approaches.md#app-007)
- Source: SRC-35

## Your Goals

### PREF-033
**A goal is an end wanted for its own sake, stated as the outcome alone.**
- Status: firm
- Rule:
  - **An end, not a means:** the party would still want it if every other goal were achieved. A step toward another goal is not a goal (the sword is a means to killing the dragon). Where the evidence supports both an end and a means, the user accepts the ambiguity (EX-036).
  - **The outcome only:** one outcome per line, with the reward that defines it ("…for Eric the Reeve's 1,000-gold bounty"). No reason or motive ("so Dunk can start his own farm"), no detail about the thing wanted, no lead, clue or source ("…shown on the party's treasure map"), no progress notes or history.
  - **No commitment level:** do not say "is considering" or otherwise rate how firmly the party took it up. A pursuit the party drops lapses (PREF-051).
  - **A job the party takes up shows its outcome:** catching the thief, not "help Quinn get back at Bentley". A bargain's reward can be part of the outcome; its technique is an opening (PREF-035).
  - **It stays active** until achieved, abandoned, replaced or failed, or its purpose is gone ("save the boy" when the boy dies). How it was established decides how it lapses (PREF-051).
  - Incidental wants are hidden by code (PREF-053).
- User's words:
  > i want to add another dimension to the rubric, maybe called top-level.   the dimension is judging that all active goals stand on their own as ends and do not ladder up to other goals.

  > update to say a goal remains active until is is achieved, abandoned, replaced or failed.  for example if the goal is "save the boy" and the boy dies, the goal is no longer active

  > the multiple 'is considering' lines are unnecessary. If they don't pursue the goal, it will fall off next time. This is not the place to track how accepted it is

  > In general, we should not be including an explanation of "Why" in goals

  > The bit about who fits in the shirt has no bearing on the shirt as a goal.  it is extra detail/precision and should be removed.

  > there is no goal about catching quinns thief

  > In general terms, I prefer that we only describe the goal, although I find its inclusion here to again be a very minor issue. It is more the general case that I am nervous about.
- Severity: a lead left in a goal ("Find the treasure marked on the party's treasure map") was judged "a very minor issue" in pass 12; the general outcome-only preference stands (SRC-60).
- Evidence: EX-035, EX-036, EX-051, EX-052, EX-056, EX-058, EX-059; [ALW-003](allowances.md#alw-003)
- History: the 2026-10-18 golden kept serious interest as "Dunk is considering buying Seamus the mule…". On 2026-10-30 (SRC-55) "is considering" was dropped: serious interest still counts, but the goal does not hedge.
- Source: SRC-07, SRC-01, SRC-55, SRC-59, SRC-60

### PREF-051
**How a pursuit was established decides how it ends.**
- Status: firm
- Rule:
  1. **Taken up or agreed** (the party took it up, or both sides agreed): it stays open until play ends it — achieved, abandoned, failed, its purpose gone, or its window passed. It survives Sessions where it is not mentioned.
  2. **Only floated, offered or one-sided** (an unaccepted challenge, a purchase being considered, an interest the characters put down): it lapses unless play renews it. No explicit cancellation is needed.
  3. **Episode-local** (mattered only within one episode): it ends when the episode ends and the party moves on (PREF-013).
  - A proposed method expiring does not by itself end the broader end it served; judge the end separately (PREF-053). An elapsed appointment ends as obsolete, not fulfilled; a missed debt deadline does not discharge the debt.
- User's words:
  > Yes I like this

  > 1) approved.  fyi, there is no explicit 'sir phidipaldi wont do this' but the next day comes and he does not go.   given that the reeve never agreed it was unlikely to ever have lasted beyond the scene anyway.

  > yes this needs to be fixed
- Evidence: EX-070 (and its pass 11 recurrence), EX-072, EX-052, EX-018
- History: proposed by the agent from the user's earlier judgments and approved 2026-11-01 (SRC-58), replacing challenge- and appointment-specific prompt wording.
- Source: SRC-58, SRC-57, SRC-59

### PREF-053
**Judge a goal's significance by what achieving its actual end would change, not by its method or the drama around it.**
- Status: firm
- Rule:
  - Distinguish the desired end from a proposed method (restoring honor, not fighting a duel).
  - A real personal end can still be too minor for the Summary: rate it incidental when achieving it would change little in later fiction. Do not borrow significance from a dramatic exchange or a larger thread.
  - When a goal is hidden as incidental, its dependent obstacles go with it unless another shown pursuit gives them a live target.
  - Do not infer an end that play or the user has not established.
  - A small desire does not become significant merely by being negotiated again; promotion needs meaningful new stakes (EX-072).
- User's words:
  > the goal here is not to have a duel, it is to restore his honor.  also i think this is too minor and not enough narrative impact (I mean that achieving the goal does not provide much narrative impact).
- Evidence: EX-081, EX-072
- History: 2026-11-01 (SRC-59) "implement then run pass 12" approved using the existing significance/incidental filter with completion-significance guidance, rather than a new threshold.
- Source: SRC-59, SRC-57

### PREF-055
**Goals are ordered by narrative priority: the adventure currently driving the party's choices comes first.**
- Status: firm
- Rule: order goals in code from classifications: adventure goals before side goals, and among adventure goals, the one currently driving the party's choices first. Do not rank by whichever action is easiest or most immediately actionable. No named-goal exception.
- User's words:
  > If there is an importance or narrative impact field, we should sort by that from highest to lowest, or sort the adventure goals first, or something

  > is it possible the ordering can be done in deterministic code?

  > Yes
- Evidence: EX-071
- History: 2026-10-31 (SRC-57) the user approved adventure-before-side ordering; 2026-11-01 (SRC-59) asked for deterministic ordering; 2026-11-01 (SRC-60) approved "put the adventure currently driving the party's choices first". Consolidated from those decisions on 2026-11-01; it had no ID before.
- Source: SRC-57, SRC-59, SRC-60

## Standing in Your Way

### PREF-034
**An obstacle is the condition that actually blocks a live goal now.**
- Status: firm
- Rule:
  - State the blocking condition and its source in one sentence, with no fix and no "why" (EX-060).
  - Not having a fix yet is not an obstacle; the fix is an opening (EX-037). Gaining a possible fix does not resolve the obstacle until it is shown to work.
  - An obstacle not yet in effect is not shown (EX-038); it may be a trouble.
  - The obstacle must actually constrain the end it is said to block: a refused method does not automatically block the broader end (EX-081).
  - It needs a live target: when the pursuit it blocks is not shown, the obstacle is not shown either. Prior approval of an obstacle does not force it into later Sessions where its goal is absent (ALW-008).
  - An unexplained refusal that blocks a pursuit is an obstacle, not a question (EX-015).
  - The link to the goal belongs in data, not glued into the text ("…; impedes: Kill the dragon", EX-039).
- User's words:
  > I think those are the same impediment for the dragon goal, but the sword one is not an impediment to a goal, it is an opportunity to overcome an impediment.

  > Can you add a new lifecycle value for impediments that are not active yet but will be in the future? Like the flying

  > OK I don't care for that as much, please revert the prompt change

  > this is good, and what i am looking for in an impediment, add that to your learnings
- Evidence: EX-037, EX-038, EX-039, EX-060, EX-081, EX-028; [ALW-008](allowances.md#alw-008)
- Source: SRC-29, SRC-55, SRC-59, SRC-60

### PREF-042
**A scene-local confrontation belongs in "Immediate danger", not also as a lasting obstacle.**
- Status: firm
- Rule: a confrontation that exists only in the final scene is told as immediate danger. A distinct continuing obstruction can still be its own obstacle.
- User's words:
  > I prefer production (i approve your recommendation)
- Evidence: EX-067, EX-021
- Source: SRC-57

## What Could Help

### PREF-035
**An opening is an extra action the party could take, which gives an advantage toward a shown goal.**
- Status: firm
- Rule:
  - It must require action to take advantage of, and it must advance a shown goal, either directly or by getting around an obstacle. An attractive offer with no goal it serves is not an opening (EX-041).
  - A goal's own price or terms is not an opening: paying it is doing the goal (EX-054; PREF-046).
  - Extra detail about an offer already listed is not a second opening (EX-053).
  - A weak link between two goals, with no action and reward actually offered, is not an opening; it may be a low-value obstacle (EX-055).
  - A plan or method toward a goal is an opening, not a promise (EX-056).
  - The shape and the benefit are defined by PREF-046; when several bullets are one opening, by PREF-045; held help, by PREF-047; implicit openings, by PREF-040; wording, by PREF-028.
- User's words:
  > an opportunity represents fundamentally an open window to gain an advantage in either overcoming an obstacle or otherwise increasing their likelihood of achieving their goal. This is inspired by the game Hitman

  > in each case, it has to be something that they have to take action in order to take advantage of.

  > I agree that it needs to tie into a goal.

  > An opportunity is an extra action that can be taken to provide an extra advantage in achieving some other goal.
- Evidence: EX-040, EX-041, EX-053, EX-054, EX-055, EX-056, EX-061
- History: on 2026-10-19 a goal link was "not necessary"; from 2026-10-24 it is required. In the 2026-10-18 golden the window and the potion are separate openings; from 2026-10-24 they are parts of the shirt plan (PREF-045).
- Source: SRC-31, SRC-08, SRC-55

### PREF-046
**An opening has the shape "if trigger, then benefit", and its benefit is an advantage toward a goal, never the goal itself.**
- Status: firm
- Rule:
  - **The benefit** is an obstacle overcome or a goal made easier. "If the party does X, they get the goal" is an approach, not an opening: searching a map's marks to find the treasure, paying a goal's price. Having a trigger is not enough.
  - **The trigger** can be an action or achieving another goal. One goal can trigger an opening toward another goal: getting armor that helps against a monster the party must fight.
  - **A plan ends at its advantage**, not at the goal: "…will stay asleep while they are in his house", not "…could take the shirt".
  - **A chain splits where it crosses into another goal** (refines PREF-045 pattern 2).
  - A benefit can be contextual and brief ("it could help against the dragon") when the capability and its use are clear; do not demand an explanation of the mechanism (ALW-004).
  - An established immediate plan that only pursues a goal directly belongs in "Where you are" if anywhere, not here.
- User's words:
  > An opportunity, generally speaking, has this: if trigger, then benefit, shape. And that's really what defines an opportunity: if the players do something or achieve some intermediate goal, it provides them with a benefit.

  > it provides a benefit that will help them overcome the obstacles that are blocking a goal or otherwise makes the goal easier to achieve.

  > One of the shapes that I definitely think we need to be looking out for is the benefit itself, not the achievement of the goal, right? This is why the treasure map failed. And why the farmer Gill and the mule failed is because it says if trigger, then not a benefit that helps them to achieve later in achieving the goal, but instead just it is a way to get the goal. And while that might be considered like an approach to achieve your goal, it is not this very specific meaning of the term opportunity.

  > Yes this works.

  > I agree. While there is a trigger here, if the party checks other locations on the map, the benefit is just that they could solve their goal, not that they will get some kind of advantage that makes achieving the goal in the future easier. This should be removed.

  > I am ok with this benefit actually
- Ambiguity the user accepts: whether a wanted item is a goal of its own or only a means to another goal can be ambiguous; when the pipeline judges it a goal, an opening from it toward the other goal is right (ALW-003).
- Evidence: EX-054, EX-074, EX-040, EX-036; [ALW-003](allowances.md#alw-003), [ALW-004](allowances.md#alw-004)
- History: 2026-11-01 (SRC-58) refined PREF-035 and replaced the earlier reading of EX-074, under which any usefulness toward another goal was a "generic benefit" to hide. 2026-11-01 (SRC-60) confirmed the direct-pursuit case.
- Source: SRC-58, SRC-59, SRC-60

### PREF-045
**One opening per plan.**
- Status: firm
- Rule: several bullets are one opening when:
  1. **Same trigger, same goal:** two bullets start from the same action and advance the same goal. Combine their benefits. They stay separate only when the benefits clearly serve different goals.
  2. **A chain is a plan:** one bullet's benefit is another bullet's trigger. Write it once, from the first trigger to the final advantage (PREF-046 says where it ends and where it splits).
  3. **Complementary pieces are one plan:** two openings each supply part of what one action needs, and the party would use them together (a way in and an owner kept asleep). When either alone would do the job, they are alternatives and stay separate.
  - Paraphrases of the same offer ("hire her" and "pay her") are one opening.
  - Boundary: different triggers with different benefits stay separate even when they serve one goal (PREF-041).
- User's words:
  > our current formula for describing opportunities is if trigger, then benefit.

  > two items that share the same trigger but have different benefits should still be described as one opportunity if both benefits are achieving, are making progress on the same goal.

  > Unless those benefits are clearly pointing at two different goals, then they should be wrapped into the same thing.

  > steps in a plan, which can often be identified because you say, if trigger one, then condition two. But then we come back and we say, if condition two, right? So using it as a trigger, then condition three or whatever.

  > you really just want to phrase it as if, you know, the first condition, you know, then we can help get to the, or if the first trigger, then it will generate the final condition we are trying to get to.

  > Yes That is definitely another pattern, and you have correctly identified it.

  > I prefer merged. Why are they not in the if.... then... Format?
- Evidence: EX-040, EX-073, EX-066 (the boundary)
- History: patterns 1 and 2 stated by the user, pattern 3 proposed by the agent and confirmed (2026-11-01, SRC-58). Merging complementary pieces reconfirmed in pass 12 (SRC-60).
- Source: SRC-58, SRC-31, SRC-57, SRC-60

### PREF-047
**Something already held is not an opening; an action that uses held help can be.**
- Status: firm
- Rule: in "if trigger, then benefit" form, a held asset has no trigger left ("if they get the shirt, they have the shirt"). Held help stays in campaign state and can be told as a gain in history (PREF-038). An action that uses it to gain an advantage is an opening: the action is the trigger.
- User's words:
  > This is an asset not an opprtunity, they have already acquired it

  > assets are not open matters, so don't (and should not) show up there.

  > Yes that works
- Evidence: EX-075, EX-048
- History: generalizes the 2026-10-31 approval (SRC-57), whose wording named two cases; the general form was proposed by the agent and confirmed 2026-11-01 (SRC-58). The earlier agent proposal to group assets and openings under one open heading was rejected.
- Source: SRC-58, SRC-57

### PREF-040
**An established option needs no explicit proposal, and an offer of help serves any goal it plainly serves.**
- Status: firm
- Rule:
  - Established access or capability and a concrete advantage can support an opening even when nobody suggested acting on it (an open window into the room where the target is). Straightforward matching of an established capability to an established need is allowed.
  - An actual offer of help serves any shown goal that what it brings plainly serves, even when the offer did not name that goal. Its conditions are its cost, not a reason it helps nothing.
  - Do not invent acceptance, negotiated terms, capability, access or cooperation (EX-055 stays rejected).
- User's words:
  > I prefer production (i approve your recommendation)

  > can you do research into the drop ded ned opportunity, which to me is the same as hilda.
- Evidence: EX-065, EX-080
- Source: SRC-57, SRC-58

### PREF-028
**An opening is shown as one short conditional sentence: "If the party does X, Y", with a specific advantage.**
- Status: firm
- Rule:
  - Combine the action and the advantage in explicit conditional form. The literal word "then" is not needed if the relation is clear.
  - The advantage says what the action gains toward the goal, not a generic ending such as "they can see what happens" (EX-061).
  - An essential uncertainty or condition may take a second short sentence.
  - Show the useful action and advantage, not a copy of the contract: for hired help, "if they hire him, he'll fight for them" can suffice without the fee or per-kill terms. The full terms stay in stored state; a fee is acceptable in history. This does not license inventing terms or hiding a material risk.
  - Keep a stated consequence; do not strip it for brevity (EX-030).
- User's words:
  > I want to add a title property to opportunities that provides a single simple sentience that combines the opening, action and potential advantage into one simple short sentence.  We are currently using just the opening, but in some cases that does not make it clear what the advantage is

  > You should be using the title not just in the table recap but in the post session matters, and then the table recap picks it up from there

  > I actually find recording the details of the contract, like the price and potentially like his payback of 5 GP per killing, to be that's much more detail and precision that I don't think needs to be included. If this is in the development section, then I think it would be fine to include the 100 gold. If this is in the opportunity section, then I think it is not necessary to define it as part of the opportunity. It is just if they hire him, you know, then he'll fight for them.

  > Great, I approve
- Evidence: EX-030, EX-034, EX-061, EX-080, EX-040
- History: 2026-10-27 one simple sentence. 2026-11-01 (SRC-59) an essential second short sentence allowed. 2026-11-01 (SRC-60) conditional form made explicit rather than preferred, and contract precision left out of the displayed opening.
- Source: SRC-39, SRC-59, SRC-60

## Still Unanswered

### PREF-003
**A question is an established unknown whose answer would be a meaningful revelation, not an ordinary gap.**
- Status: firm
- Rule:
  - It is established by the fiction, and its answer promises a meaningful narrative revelation and could be a worthwhile investigative objective.
  - **Ordinary unknowns are not questions:** an unidentified creature, an unexamined item's powers, missing tactical information, routine gaps (EX-002).
  - **Undisclosed information is not a question:** a remark that more exists ("the dragon is only the first of my problems"), or knowing who holds a secret and its price, establishes no subject (EX-014, EX-016).
  - **An unexplained refusal or decision is not a question** unless the evidence makes the reason itself strange (a contradiction, a lie, a pattern); usually it is an obstacle (EX-015).
  - **Ask the underlying question, not its clue:** "Where and what is the treasure?", not "Which marked location holds it?" (EX-017).
  - **Form:** one bare open-ended question of about ten words, with no clue, source or relevance attached (EX-019, EX-062).
  - An evocative wording must not raise its ratings; rate the evidence (EX-020).
  - A grounded, unexplained change in the world (hidden creatures appearing more often) is a candidate (EX-062 follow-up).
  - A question does not need the characters to have expressed interest, and it does not require danger.
  - Adventure-defining questions are protected from the payoff filters (PREF-054). Questions end as PREF-013 and PREF-051 say.
- User's words:
  > A **Mystery** is an unresolved question established by the fiction whose answer promises a meaningful narrative revelation and could serve as a worthwhile investigative objective for the player characters.

  > **Ordinary unknowns are not mysteries.** Missing tactical information, unidentified objects, unknown abilities, and routine information gaps do not qualify unless their answers promise a meaningful narrative revelation.

  > Neither feel to me like investigative targets. Yes they are unknowns, but they are not questions the party is existed to find out for its own sake.

  > can you add a filtering attribute for whether the question is open ended, like "why is the king raising an army?" versus close yes/no or how many out how much questions

  > Your recommendation is certainly my preference, but again, another minor issue.
- Severity: clue-framed wording of an otherwise eligible adventure question was judged "another minor issue" in pass 12 (SRC-60).
- Evidence: EX-002, EX-014 to EX-020, EX-062; [ALW-002](allowances.md#alw-002), [ALW-007](allowances.md#alw-007)
- History: rewritten 2026-10-25 from the user's own definition file and 54-case testbed ([APP-010](approaches.md#app-010), [APP-011](approaches.md#app-011)). The goldens' "What happened to Gill's sons?" is no longer required on current evidence (ALW-007).
- Source: SRC-34, SRC-32, SRC-33, SRC-59, SRC-60

### PREF-054
**Adventure-level questions are not lost to the low-impact filters.**
- Status: firm
- Rule: a grounded, open-ended, investigable question that defines a shown adventure goal (where and what the treasure is) is published without needing independent depth or payoff ratings. It must still pass grounding, investigability, question-type and goal-link checks. This does not exempt ordinary unknowns that merely sit on an adventure thread.
- User's words:
  > this is more bothersome for me, because adventrure level goals should be excluded from the low impact filter
- Evidence: EX-017, EX-062
- History: stated 2026-11-01 (SRC-59); "implement then run pass 12" approved this adventure-objective question path.
- Source: SRC-59

### PREF-013
**An episode-local question ends when its episode ends and the party moves on.**
- Status: firm
- User's words:
  > I was expecting these to be marked obsolete one they left the barrow mound
- Evidence: EX-018
- Source: SRC-34

## Promises and Debts

### PREF-036
**A promise or debt is something the party owes that a recipient has a claim on: specific, finite, and something the recipient actually cares about.**
- Status: firm
- Rule:
  - Only what the party owes. What someone owes the party is an asset or an opening (PREF-020, PREF-038).
  - A method the party agreed to try toward a goal is an opening, not a promise (EX-056).
  - The recipient must have a stake in the specific act, not only in the broader outcome it might serve: acknowledging advice ("I will make sure that I bring my Lance") is not a promise to the adviser (EX-042).
  - Completing the activity around a deal does not discharge what is owed (EX-044).
  - The test is PREF-052. Whether to hide low-stake commitments is deferred (see below).
- User's words:
  > The lake thing is not a commitment, it is just phidipaldis acknowledging George's advice. George does not care or have a stake in him using his lane.

  > The field should be type of commitment and some values should for sure include general agreement, which is what happens if somebody, you know, suggests an approach and a player just agrees to the approach. … I want to filter out general agreement.

  > Now, can you add another property called stake, which is how much of a stake the person obligated to whom the obligation is owed has in you fulfilling the specific terms of this oath?

  > this is a section for the party making a Promise or owing a debt, not situations where somebody owes a debt or makes a promise to the party

  > Yes we could also try Filtering out the low-stakes commitments. Can you please add a work item to explore this? Which we can come back to after we're generally happy with other stuff.
- Deferred: exploring the exclusion of `low` as well as `trivial` stake is registered ([work item](../.work-items/filter-low-stakes-commitments/)) for after other output quality is satisfactory. Until then, real low-stake obligations remain eligible (ALW-009).
- Evidence: EX-042, EX-043, EX-044, EX-056, EX-076; [ALW-009](allowances.md#alw-009)
- Source: SRC-10, SRC-41, SRC-55, SRC-57, SRC-60

### PREF-052
**A promise exists only if not doing it would break faith with someone who has a claim on that specific act.**
- Status: on trial
- Rule: agreeing with advice, showing you value someone's opinion, or saying you plan to come back gives nobody a claim. A word like "vow" in an upstream paraphrase doesn't decide it; what was actually said, and who relies on it, does. A personal promise can qualify without a formal oath or contract.
- User's words:
  > I am fine to try your proposal or breaking faith

  > this is not a debt, it was just an agreement.  If the party or Sir Phidipaldi never goes back, he is not breaking an oath or contract

  > We still get the whole bringing the lance to the dragon vow from Sir Fittipaldi as a promise in debt. I feel like this is an edge case, and I wouldn't do any unnatural acts to fit it, but I don't think that he meant this as an actual vow or promise. Promise or obligation to the woodsman. He was just saying that he was agreeing and showing the woodsman that he valued the woodsman's opinion. And the woodsman actually has no stake and doesn't really care about the lance. And so it didn't really feel like a commitment.
- Watch: revisit if it lets through, or hides, commitments the user judges differently.
- Evidence: EX-042, EX-076, EX-056
- Source: SRC-58, SRC-57

### PREF-020
**A promise with no end is something that happened, not an open matter.**
- Status: firm
- Rule: a promise never to do something, or a recurring duty, can never be crossed off. It can be told in history but is never an open promise. Payment owed to the party is an asset if nothing is needed to collect it, and an opening if action is needed.
- User's words:
  > The problem with recurring terms or negative terms like 'I will not reveal your presence to king hogboon" is they and never be completed.

  > a promise not to do something is actually a promise and could be treated as a development in the past tense, but is never an open matter, so we just need a property that can filter on, you know, has definite end or something.

  > I think you can treat money owed to the party as an asset if there's nothing that they need to do to get it, and an opportunity if there's something they need to do to be able to collect.
- Evidence: EX-043, EX-056
- Source: SRC-10, SRC-55

## Meanwhile

### PREF-037
**A trouble is an established, developing harm from outside the party that the party could affect.**
- Status: firm
- Rule:
  - **Established:** play or the adventure establishes danger or developing harm absent intervention. A plausible risk inferred from someone's activity is not enough (someone out hunting a monster is not thereby in danger).
  - **A harm, not a lost benefit:** someone else winning a prize, reward or loot first is not a trouble.
  - **Articulated:** a specific harm, not mischief in general.
  - **External:** the party's own scheme going wrong is not a trouble.
  - **Not an opening:** someone dangerous offering their services is an opportunity, however disturbing.
  - **Worded without overstating:** name what is established and let the danger follow; do not predict actions the evidence doesn't support (EX-050).
  - No request for help, accepted quest or player action is required when danger is established.
  - Recurring and continuing harms are temporarily allowed.
  - A live threat at the stopping point is told once (PREF-004); a scene-local confrontation is immediate danger (PREF-042).
- User's words:
  > My point about no expectation or ask for help is that this is *not* an unfolding rescue problem, and was trying to find a litmus test for establishing that.

  > my only push back here is that this is existing trouble more than brewing trouble.

  > Right he is actually an opportunity (albiet a disturbing one) for the party, not a danger that the party has to stop

  > something can't be a trouble if the party itself (like dunk) is the source of the trouble

  > Yes, someone else might win a potential future goal that they have, but just failure to achieve a goal if it doesn't have narrative trouble to it beyond just the party acquiring new good stuff is not itself a trouble.

  > Yes, absolutely. This is not about whether or not the players took action; it's about the way the adventure frames Gil's sons.
- Unsettled: whether a recurrence of an existing harm counts; recurring and continuing harms were "temporarily" allowed on 2026-10-23.
- Evidence: EX-045, EX-046, EX-050, EX-063; [ALW-010](allowances.md#alw-010)
- History: 2026-11-01 (SRC-60) the established-danger and lost-benefit boundaries were added after the user's interview about Gill's sons.
- Source: SRC-26, SRC-01, SRC-60

## Where You Are and Immediate Danger

### PREF-031
**"Immediate danger" is reserved for immediate, genuine threats. It may be empty.**
- Status: firm
- Rule: only a threat to the party right now at the stopping point. When nothing threatens them, the section says so; the user's golden has "None."
- User's words:
  > Load the work item to reserve immediate danger for genuine threats.
- Evidence: EX-050, EX-067
- Source: SRC-44, SRC-01

### PREF-056
**"Where you are" places every character and includes an established immediate intention.**
- Status: firm
- Rule:
  - When the party is split, place every player character, one short sentence per group (EX-064).
  - Include the immediate intention play resumes with (heading to a place, trying to persuade someone), but only when it is established. Do not invent a plan to fill the slot, and do not claim an agreement nobody gave. It is a next action, not another goal.
  - Leave out secondary detail that fails PREF-050.
- User's words:
  > starting position: all good

  > They have an immediate goal of going to the barrow (or maybe of convincing brother dirk to come with)

  > 8) approved, if there is one
- Evidence: EX-064, EX-077, EX-078 (pass 11 recurrence)
- History: consolidated 2026-11-01 from the pass 5 judgment (SRC-55) and the approved pass 7 recommendation (SRC-57); it had no ID before.
- Source: SRC-55, SRC-57
