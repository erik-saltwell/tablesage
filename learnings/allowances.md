# Allowances

Particular occurrences the user looked at and accepted, even though a check might flag them. A review must not report an allowed occurrence, or one essentially the same, as a finding. Other occurrences of the same pattern are still judged normally: an allowance is not a change to the rule. Rule-level relaxations live in the rule itself in [preferences.md](preferences.md).

"Essentially the same" means the same element of the same Session (the same person, offer, question or event under the same heading), even if a later pass words it differently. An allowance stops applying when its **Ends if** condition is met, or when the user withdraws it.

Each entry gives:
- **Accepted:** the exact text (or, for an omission, what is missing), with Session, pass and heading.
- **User's words:** verbatim.
- **Firmness:** `firm`, `for now` or `tentative`. All three are excluded from review findings; firmness tells you how readily the user may revisit it.
- **Does not extend to:** what the allowance must not be stretched to cover.
- **Checks:** the review-guide checks it would otherwise trigger, when known.

### ALW-001
**A brief descriptor at a person's first mention in the Summary.**
- Accepted: pass 12, Session 002, "What could help": "Drop Dead Ned, a murderous thief, offers to join the party for 100 gold a week if he gets to kill people. Dr. Uriah is thinking it over." The aside "a murderous thief" at Ned's first mention in that Summary.
- User's words:
  > Ooh, I don't know how I feel here. I think maybe if it's the first time we mention Ned in the summary, then it is fine to add that little aside.
- Firmness: tentative
- Does not extend to: repeated introductions within one Summary, stacked labels, or profiles of traits. It does not make a descriptor mandatory. It does not approve the fee and per-kill terms in an opening (PREF-028).
- Checks: RC-075 (formerly RC-060 for this occurrence)
- Rule: [PREF-049](preferences.md#pref-049). Source: SRC-60; [EX-080](examples/what-could-help.md#ex-080-a-paid-offer-of-help-hidden-because-it-didnt-name-the-goal)

### ALW-002
**No dragon-origin question in Session 001.**
- Accepted: pass 11, Session 001, "Still unanswered": the question of where the black dragon came from, or how it relates to the dragon Sir Brandon killed, is absent.
- User's words:
  > this is actually fine for me for now
- Firmness: for now
- Does not extend to: Session 002 or later, where losing a previously shown dragon-origin question is worth fixing ("agreed this is worth fixing", SRC-59). It does not prohibit including the question in Session 001.
- Checks: SE-005
- Rule: [PREF-003](preferences.md#pref-003). Source: SRC-59; [EX-062](examples/still-unanswered.md#ex-062-session-001s-mysteries-under-the-unified-pipeline)

### ALW-003
**Warwick's mithril shirt as a goal of its own, with an opening from it toward the dragon.**
- Accepted: Session 002, when the pipeline classifies getting the shirt as a goal: the shirt goal, plus an opening of the form "If the party gets Warwick's mithril shirt, it could help against the dragon."
- User's words:
  > There is an interesting discussion here about whether or not getting Warwick's shirt is itself its own goal or only a means to help them in fighting the dragon. But I actually think this is an ambiguous case, and if you assume that Warwick and, wait, and if the pipeline judges Warwick's shirt as being its own goal, then I think these two bullets make total sense.
- Firmness: firm (an accepted ambiguity)
- Does not extend to: other means listed as goals (the sword stays a means), or duplicate shirt openings (PREF-045). Classifying the shirt as only a means to the dragon is also acceptable.
- Checks: SE-035, RC-029
- Rule: [PREF-033](preferences.md#pref-033), [PREF-046](preferences.md#pref-046). Source: SRC-58; [EX-036](examples/your-goals.md#ex-036-whether-the-mithril-shirt-is-its-own-goal-flips-between-runs)

### ALW-004
**The shirt's contextual benefit, "it could help against the dragon".**
- Accepted: pass 11, Session 002, "What could help": "Dunk says he has a plan to get Warwick's mithril chain shirt. If he gets it, it could help against the dragon."
- User's words:
  > I am ok with this benefit actually
- Firmness: firm
- Does not extend to: vague benefits in unrelated openings ("they can see what happens", EX-061), or every other clause of the bullet.
- Checks: SE-031, SE-036, RC-069
- Rule: [PREF-046](preferences.md#pref-046). Source: SRC-59; [EX-074](examples/what-could-help.md#ex-074-a-goal-restatement-or-generic-item-benefit-is-not-another-opening)

### ALW-005
**Map marking told as an event.**
- Accepted: pass 11, Session 002, "Last session...": "Father William marked the witch's home and the Barrow Mound on the party's map."
- User's words:
  > agree this is not a revelation, but ok as a developments
- Firmness: firm
- Does not extend to: telling it out of play order (PREF-027).
- Checks: RC-067 (retired), RC-072
- Rule: [PREF-039](preferences.md#pref-039). Source: SRC-59; [EX-011](examples/last-session.md#ex-011-useful-location-approved-then-excluded)

### ALW-006
**The mule offer inside Dunk's encounter with Farmer Gill.**
- Accepted: pass 12, Session 001, "Last session...": "Dunk drank with Farmer Gill, who offered him a mule and told how Sir Brandon once slew a dragon." Including or omitting the short mule-offer detail is acceptable.
- User's words:
  > I am actually fine with this either way.
- Firmness: firm
- Does not extend to: a mule goal or opening, or incidental detail in other encounters.
- Checks: RC-016, SE-001 (the mule-detail portion only; the missing challenge history is separate)
- Rule: [PREF-039](preferences.md#pref-039), [PREF-050](preferences.md#pref-050). Source: SRC-60; [EX-079](examples/last-session.md#ex-079-dunks-visit-to-farmer-gill-disappears-as-a-historical-event)

### ALW-007
**No question about Gill's sons.**
- Accepted: "What happened to Gill's sons?", which the user's Session 001 and 002 goldens include, is absent.
- User's words: the agent recommended allowing the omission because the sons' known expedition establishes no mysterious disappearance; the user replied:
  > Agreed
- Firmness: firm, on current evidence
- Does not extend to: Sessions where new evidence establishes an unexplained disappearance or another hidden truth about the sons. It does not make the sons a trouble (EX-045).
- Checks: SE-015 (the sons portion only)
- Rule: [PREF-003](preferences.md#pref-003). Source: SRC-60; [EX-019](examples/still-unanswered.md#ex-019-golden-mysteries-bare-questions-about-underlying-truths)

### ALW-008
**No obstacle about Warwick refusing to sell the shirt, when no shirt goal is shown.**
- Accepted: pass 12, Session 001, "Standing in your way": the earlier approved "Farmer Gill says Warwick always refuses to sell his mithril chain shirt" is absent, because no live shirt pursuit is established.
- User's words, agreeing with "A refusal should appear as an obstacle only when it blocks something the party wants. Your earlier approval shouldn't force that fact into every later generation regardless of which pursuits are established.":
  > That matches
- Firmness: firm
- Does not extend to: Sessions where a shirt pursuit is shown; then the refusal is the target obstacle (EX-060). Do not infer a shirt goal to keep the obstacle.
- Checks: SE-008, SE-014
- Rule: [PREF-034](preferences.md#pref-034). Source: SRC-60; [EX-060](examples/standing-in-your-way.md#ex-060-an-unexplained-refusal-stated-as-the-obstacle)

### ALW-009
**Dr. Uriah's penance as a promise.**
- Accepted: pass 12, Session 002, "Promises and debts": "Dr. Uriah must give penance at Brandon's Barrow Mound, as Father William asked."
- User's words, asked whether keeping it is acceptable for now:
  > Yes
- Firmness: for now (until the deferred low-stakes investigation decides otherwise)
- Does not extend to: promises inferred from agreement or advice, such as the lance (EX-042), or a stale penance after it is done.
- Checks: RC-053, SE-017
- Rule: [PREF-036](preferences.md#pref-036). Source: SRC-60; [EX-042](examples/promises-and-debts.md#ex-042-acknowledged-advice-recorded-as-a-promise-twice)

### ALW-010
**Gill's sons mentioned in the dragon trouble.**
- Accepted: pass 5, Session 001, "Meanwhile": "A small black dragon roams outside Brandonsford and took the woodsman George's arm. Gill's three sons are out trying to kill it."
- User's words:
  > troubles: this is good.   I don't need the sons part to describe the danger of the dragon to the town, but its fine like this too
- Firmness: firm
- Does not extend to: the sons as a trouble of their own (EX-045).
- Checks: RC-016, SE-006
- Rule: [PREF-037](preferences.md#pref-037). Source: SRC-55; [EX-063](examples/meanwhile.md#ex-063-the-dragon-as-session-001s-trouble)
