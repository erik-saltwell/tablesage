# Review, regenerate, and export a Session

Once a Session has been [processed](../concepts/session-processing.md), Session
Detail is where you check what TableSage produced, rebuild outputs after a
change, take copies out of TableSage, and clear a Session to start again. This
page covers those actions. Campaign-wide regeneration is covered at the end.

## Read the Artifacts panel

The **Artifacts** panel on Session Detail lists the user-facing
[artifacts](../concepts/sessions.md#session-artifacts) and marks each one:

| Mark | Meaning |
|---|---|
| ● | Current: it exists and is up to date with everything it was built from. |
| ◐ | Out of date: it exists, but something it depends on has changed since. |
| ○ | Missing: it hasn't been produced yet. |

An out-of-date artifact is still on disk and can still be exported. Reprocessing
or regenerating brings it up to date. See
[Session processing](../concepts/session-processing.md#how-a-run-behaves) for what
makes a step out of date.

Problems from the actions on this page appear in the **Errors** table on the same
screen. Problems from Process Session appear on that screen's rows instead.

## Regenerate an artifact

Use this when you want TableSage to write an output again without redoing
the reviews, for example after you change an attendee's Role.

1. On Session Detail, press **?** to open **Other actions**, then choose
   **Regenerate Artifact** (**R**).
2. Choose what to rebuild: **Role Transcript**, **Transcript Sections**,
   **Ledger + Scene Breakdown**, **Player Introductions**, **Recap Summary**, or
   **Summary**.
3. Confirm. TableSage rebuilds the artifact you chose and updates the outputs
   that depend on it.

Regenerate Artifact is available only when the Session has a current reviewed
transcript, because every generated output is built from it. It runs as a normal
processing run, so it can't overlap another one; if processing is already
running, TableSage tells you to wait.

If the change you made was to a *review*, such as a name correction or a
transcript edit, open Process Session and restart that step instead. See
[Session processing](../concepts/session-processing.md#how-a-run-behaves).

## Export an artifact

**Export** copies an artifact out of the Session so you can use it elsewhere.
It never moves or changes the original.

1. Press **?**, then choose **Export** (**X**). It is available once at least one
   artifact exists.
2. Choose an artifact and press **Enter** (or **E**).
3. Choose where to save it.

You can stay on the Export screen and export several artifacts in a row. Two
details to know:

- If the artifact is out of date, TableSage warns you and asks whether to export
  it anyway.
- The **Ledger** can be exported as **JSON** (the structured record) or
  **Markdown** (a readable version). You are asked which you want.

## Clean a Session

**Clean Session** (**C** under **Other actions**) deletes every artifact
TableSage has produced for the Session, **including the imported input audio**,
and clears its processing progress. The Session itself, its attendance, and its
Roles remain.

Use it to start a Session over from the audio, or to reclaim disk space.
TableSage always asks you to confirm first, and it can't be undone. It is
unavailable while processing is running, or when there is nothing to delete.

To remove one voice clip or one Session, see
[Delete and clean up](../concepts/delete-and-clean.md).

## Extract glossary terms on demand

**Extract Glossary** (**L** under **Other actions**) runs the glossary extraction
again from Session Detail. It restarts the *Suggest Glossary Terms* step, so you
review proposed terms, and anything the new terms affect is refreshed by the
usual steps. See [Campaigns and glossaries](../concepts/campaigns.md#building-the-glossary).

## Regenerate every Session in a Campaign

On Campaign Detail, **Regenerate All Outputs** (**O** under **Other actions**)
checks every Session in the Campaign that has imported audio and rebuilds
whatever is missing or out of date, oldest Session first. A progress dialog shows
which Session and which output it is working on.

Sessions whose transcript review isn't complete are skipped, and the
message shown when it finishes says how many. If no Session has a completed review, nothing
is generated. Use this after upgrading TableSage (updated prompts mark existing outputs out of
date), and before building
[Previously On or Opportunities](prepare-the-next-session.md), which need every
Session's scene breakdown to be current.
