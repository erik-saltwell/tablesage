# Overview

Create a compact, player-facing recap of the current Session represented by the supplied Session Ledger.

Describe only what happened in this Session. Do not reproduce or reconstruct the spoken recap from the beginning of the recording, and do not recap earlier Sessions. This is an intentionally minimal placeholder prompt; do not infer additional length, selection, voice, or presentation requirements beyond the rules below.

# Input Description

You will be provided with four inputs:

- `<session_metadata>`: the campaign name, game system when known, and Session date when known. Use this only for orientation; it cannot establish an event or fact.
- `<session_attendees>`: each human attendee followed by zero or more roles played in this Session. Use this only to interpret player and character names already present in the Session Ledger.
- `<glossary>`: campaign terms with optional descriptions. Use this only to recognize and spell terms already present in the Session Ledger. It cannot establish an event or fact.
- `<session_ledger>`: the complete canonical Ledger v4 for the current Session. This is the sole source for claims about what happened.

Do not treat Session metadata, attendee mappings, or glossary descriptions as evidence that something occurred. Do not add events, outcomes, motivations, or connections that are absent from the Session Ledger.

# Scene Rules

- Produce exactly one output bullet for each scene represented in the Session Ledger.
- Give each bullet a short description of the scene.
- Follow the scene description with one sentence summarizing what happened in that scene.

# Example

For a Session Ledger containing one scene at a city gate and one scene in a council chamber, a valid response is:

- At the city gate. The party persuaded the watch captain to let them enter after presenting the recovered seal.
- In the council chamber. The council accepted the party's warning and agreed to evacuate the riverside district.

# Output Format

Return only a flat sequence of Markdown bullets. Every bullet must begin with `- `.

Do not include a title, a `## Recap` heading, nested bullets, opening-preamble text, commentary, or a Markdown code fence. The application adds the `## Recap` heading deterministically.
