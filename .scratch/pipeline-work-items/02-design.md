# Design: "Question" Ledger event type

Design notes from a brainstorm session (2026-09-01), resolving
[02-question-ledger-event.md](02-question-ledger-event.md)'s open questions. This is the
implementation-ready spec for that item, and it supersedes some of that item's original acceptance
criteria (see "Changes from the original work item" below).

## Summary

Question is a sixth discriminated Ledger type, but it is not a peer of the other five in the way
the work item originally assumed. Narration/Action/Speech/Expression/Correction are all in-fiction
moves, carrying a `source` that is a role or character. Question is a **meta move**: a player
breaking character to ask about game/world state, and (optionally) another player resolving it.
It does not have a `source`; it has `asker`/`question` (mandatory) and `resolver`/`resolution`
(optional, both-or-neither).

Question is the out-of-game counterpart to Action's proposal/uptake pattern (§5 of the format doc):
Action proposes a deed that auto-canonizes unless contested; Question proposes an inquiry that
becomes canon only if answered. The admission test for whether a Question belongs in the Ledger at
all is the same "does it add to or change fiction" test the other types are held to — see
"Classification: Question vs. omitted" below.

## Why this required reopening the upstream gate, not just the schema

The format doc (`canonical_ledger_format_v3.md` §3) currently states: "OOG, mechanical talk, and
query utterances still never enter the ledger." That's now wrong as a blanket rule. The gate splits
three ways:

- **Chit-chat** ("how was your trip?") — omitted, unchanged.
- **Mechanics-only** ("what's my AC bonus," "was that a 19?") — omitted, unchanged.
- **Game/world-state clarification** ("how old is this guy?", "does he look like he trusts me?")
  — now admitted as Question, when the answer would add or change fiction.

This gate is not a separate code path — `generate_ledger`'s conversion is one structured-output LLM
call over the whole role-rendered transcript (§8), and the gate is prompt guidance inside
`generate_ledger/system.md`. Updating the three-way split is a prompt change in the same file the
work item already needs to touch, not new pipeline surgery.

## Classification: Question vs. omitted

**Test:** does the question/answer pair, taken together, add or change something about the
fictional world's state? If yes, however the question is phrased, it's a Question. If the answer
would only restate rules, describe a die result, or repeat information already established in the
session, it's omitted.

- "Is the door locked?" → "No, it's ajar." Question (new world-fact).
- "How old is this guy?" → "Maybe sixty." Question (new world-fact).
- "Does he look like he trusts me?" → "Hard to tell, honestly." Question (fiction, even though the
  answer is inconclusive — the GM's read on an NPC's demeanor is world-fact).
- "What's my modifier for that roll?" → omitted (mechanics).
- "Was that a 19?" → omitted (mechanics, rehashing already-known information).
- "Did you just say the door was locked?" → omitted (rehash of already-established fact, not new
  content).
- A rhetorical question with no plausible world-fact answer → omitted; no special-casing needed,
  it just fails the test because there's nothing to resolve.
- A question answered in the same breath ("Is he friendly? — no, he sneers") → a single Question
  entry with `resolver`/`resolution` filled from the same beat. No separate handling needed.

**In-fiction questions stay Speech, not Question.** A character asking another character something
in voice ("What's behind the door?" spoken as Bran) is still Speech — Question is specifically the
OOG, player-breaking-voice move. The type discriminator, not phrasing, is what distinguishes an
in-fiction utterance from a table-level one.

**No duplicate Narration.** A resolved Question that adds world-fact is recorded once, in the
Question entry. It is not also written out as a separate Narration entry. This matches the
"derived world-state" cost the format doc already accepts for Action (§8) — a reader reconstructs
settled canon by walking Actions *and* Questions, not just Narrations. Duplicating into Narration
would be the "Assert vs. Resolve" mistake in miniature (§7): recoverable from adjacency, no new
reading protocol, pure redundancy.

## Schema

```python
class Question(_StrictModel):
    type: Literal["question"]
    asker: NonEmptyText = Field(description="The player asking, by name, not the in-fiction character or role.")
    question: NonEmptyText = Field(description="What was asked.")
    resolver: NonEmptyText | None = Field(description="The player who resolved it, by name, if resolved.")
    resolution: NonEmptyText | None = Field(description="The resolving answer, if resolved.")

    @model_validator(mode="after")
    def _resolver_and_resolution_together(self) -> Self:
        if (self.resolver is None) != (self.resolution is None):
            raise ValueError("Question.resolver and Question.resolution must both be set or both be absent.")
        return self
```

`Question` subclasses `_StrictModel` directly, **not** `_LedgerUtterance` — it has no `source`.
`LedgerUtterance` becomes `Narration | Action | Speech | Expression | Correction | Question`
(discriminated on `type`, `"question"` lowercase per the existing convention).

`asker`/`resolver` hold the **player's name**, not a role or in-fiction character — this is the one
type in the Ledger that intentionally reintroduces human identity, deliberately reversing the v2→v3
decision to strip it (§9's migration note). If the model puts a role or character name there
instead, that's tolerated, not rejected — it degrades gracefully rather than needing strict
validation.

## Envelope change: `attendees`

`asker`/`resolver` need something to be checked against, and the Ledger becomes self-contained
(readable later without a DB round-trip) rather than depending on prompt-only context. `Ledger`
gains a new top-level field:

```python
class Attendee(_StrictModel):
    player_name: NonEmptyText
    roles: tuple[NonEmptyText, ...]

class Ledger(_StrictModel):
    version: Literal[3] = 3
    session_id: uuid.UUID
    session_name: NonEmptyText
    attendees: tuple[Attendee, ...]
    preamble: Preamble | None
    utterances: list[LedgerUtterance]
```

Sourced from `sessions.list_attendance()` (`entities/sessions.py`), which `Application.generate_ledger`
already calls to build `known_roles` — no new data model, just a second thing built from the same
call and threaded through.

## Warning-check: a second counter, not a shared one

The existing `_role_warning_count` checks `source`/`character` against `known_roles`. Question has
no `source`, so it needs its own check against `attendees`' player names, not the role list:

```python
def _attendee_warning_count(response: LedgerGenerationResponse, known_players: frozenset[str]) -> int:
    warning_count = 0
    for utterance in response.utterances:
        if isinstance(utterance, Question):
            warning_count += utterance.asker not in known_players
            if utterance.resolver is not None:
                warning_count += utterance.resolver not in known_players
    return warning_count
```

`generate_ledger()`'s retry logic sums both counts (`_role_warning_count` + `_attendee_warning_count`)
for candidate selection — no change to the three-attempt/fewest-warnings mechanism itself, just a
second source of warnings feeding the same total.

## Changes from the original work item

The original work item (`02-question-ledger-event.md`) assumed Question would follow `_LedgerUtterance`
exactly (`source` field, participating in `_role_warning_count` unchanged) and mirror `Speech`'s
`entity`/`statement` shape. Both turned out to be wrong once "what does a question's `source` even
mean" was pressure-tested:

- Question has no `source` — it has `asker`/`question`/`resolver`/`resolution`, checked against a
  new `attendees` list, not the role list.
- The upstream gate's "query utterances never enter the ledger" rule (§3) needs updating to the
  three-way split above, not left as-is.

## Files expected to change

- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py` —
  add `Question`, `Attendee`; extend `LedgerUtterance` union; add `Ledger.attendees`; add
  `_attendee_warning_count`; thread attendee names into `LedgerPromptData` and `generate_ledger()`'s
  signature; combine both warning counts in the retry loop.
- `packages/tablesage-application/src/tablesage_application/application.py` — `generate_ledger`
  (~line 447): pass `attendees` (already fetched for `known_roles`) into
  `generate_ledger_pipeline.generate_ledger` and into the constructed `Ledger`.
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/system.md`
  and its template — teach the three-way chit-chat/mechanics/world-state split, Question vs. Speech
  (OOG vs. in-fiction), the no-duplicate-Narration rule, and how `attendees` maps to `asker`/`resolver`.
- `.documentation/canonical_ledger_format_v3.md` — add Question to §5's type table and prose, update
  §3's "query utterances never enter the ledger" line to the three-way split, add `attendees` to the
  §4 envelope table, record the `source`-reversal-for-Question decision in §6 or a new subsection,
  and log the rejected "duplicate into Narration" alternative in §7.
- Tests: `packages/tablesage-application/tests/session_pipeline/test_generate_ledger.py` — schema
  round-trip for `Question` (rejects extra fields, enforces resolver/resolution pairing, participates
  in the discriminated union), `_attendee_warning_count` behavior, and a generation-flow test with a
  stubbed response containing a `Question` entry (both resolved and unresolved).
