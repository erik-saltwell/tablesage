# New player from session — quality rubric

## Subject and intended effect

This rubric judges the experience of creating a player while adding attendees to a session, and of communicating each player's voice-sample count in the session-detail and player-list screens. It values keeping session setup in context, making absent voice samples apparent, and presenting their absence as a non-blocking warning.

## Shared scale

Each dimension uses a 0–10 scale, where higher is better. Intermediate scores may be used when supported by reasoned evidence. The dimensions are independent; this rubric has no total score, weights, targets, or pass/fail threshold.

## Dimensions

### In-flow attendee setup

Rewards preserving the user's session-setup context while they create a needed player and add them as an attendee.

- **0:** Creating a needed player requires leaving or abandoning session attendee setup.
- **5:** A player can be created from the session context, but returning to the attendee task is awkward or loses context.
- **10:** A missing player can be created while adding attendees, then immediately selected or added without leaving the session flow.

### Voice-sample status clarity

Rewards fast, consistent recognition of a player's voice-sample count and of the zero-sample state.

- **0:** Counts are absent, hidden, or zero is indistinguishable from a populated player.
- **5:** Counts are visible but difficult to scan, inconsistent between screens, or zero needs interpretation.
- **10:** Voice-sample count is the leading, easy-to-scan column in both screens; a zero is visibly distinguished by tinting only the numeral red.

### Non-blocking warning tone

Rewards treating zero voice samples as something worth noticing, without making it appear to be a failure or prerequisite.

- **0:** A zero sample count looks like a failure, validation error, or action the user must resolve.
- **5:** It attracts attention but the UI's implication about whether to continue is ambiguous.
- **10:** Zero samples are plainly a warning to investigate later; surrounding copy, styling, and controls make continuing feel normal and permitted.

## Calibration boundary

An implementation that creates players inline and makes zero conspicuous but disables forward progress scores poorly on **non-blocking warning tone**, even if it scores well on setup flow and status clarity. An implementation that creates and adds players inline, shows zero as a red numeral in the count column, and retains ordinary forward controls represents the preferred boundary: conspicuous warning without error semantics.
