# Prepare the next Session

TableSage can use a Campaign's history to help you get ready for the next
Session. Two tools on Campaign Detail read the **scene breakdowns** of your
earlier Sessions (the scene-by-scene record produced by
[Generate Artifacts](../concepts/session-processing-returning-players.md#generate-artifacts)):

- **Create Previously On** helps you pick the scenes worth recalling and writes a
  short "previously on…" recap you can read to the table.
- **Generate Opportunities** suggests established campaign elements that could
  return in a useful or surprising way in the Session you have in mind.

Both use your **High** model (see [Update your settings](settings.md)) and send
Campaign text to that provider (see [Privacy](../reference/privacy.md)). Neither
saves anything inside TableSage; what you produce is a Markdown file you keep.

## What you need first

Every Session in the Campaign must have a **current, complete scene breakdown**.
That means each Session has been processed through **Generate Artifacts** and
hasn't gone out of date since. If any Session doesn't qualify, TableSage stops and
lists which Sessions have a problem and why. The usual fix is to run
**Regenerate All Outputs** on Campaign Detail (see
[Review, regenerate, and export a Session](review-and-export.md#regenerate-every-session-in-a-campaign)),
then try again.

Both tools are found under **Other actions** (**?**) on Campaign Detail.

## Create Previously On

Choose **Create Previously On** (**V**). The tool works in two stages.

**1. Say what is coming.** TableSage reads the Campaign and shows:

- **Starting situation**, pre-filled from where the last Session ended. Edit it to
  match how you actually plan to open.
- **What might happen next Session?** Your notes on where play may go.
- **Campaign ingredients**: up to five candidates in each of *People & Factions*,
  *Threads & Commitments*, *Active Pressures*, and *Places & Objects*, each with its
  current state. Focus one to read the scenes it comes from. Press **Space** or
  **Enter** to select the ones that matter.

Select at least one ingredient or write some notes, then choose **Find Scenes**.
If a suggestion is wrong, correct it in your notes.

**2. Choose the scenes.** TableSage recommends scenes from across the Campaign,
starred **★ Scout**, with a rationale for each that only you see. The list shows
every Session and its scenes. Press **Space** or **Enter** to add or remove a
scene, or to expand a Session, and focus a scene to read its full record. You may
choose any scenes, not only the recommended ones.

Choose **Save Markdown…**, pick a destination, and TableSage writes a concise
recap of only the scenes you chose. The suggested filename names the Campaign and
the next Session number. If the file already exists, you are asked to replace it,
and the old file stays intact until the new one is written. If saving fails, fix
the cause and choose **Retry Save**.

**Back** returns to stage one. **Exit** (or **Esc**) asks before discarding your
inputs, because this tool does not keep drafts.

## Generate Opportunities

Choose **Generate Opportunities** (**Y**). TableSage shows where the Campaign
currently stands (its ending situation) and asks **What might happen next
Session?** Describe the situation you expect, then press **Ctrl+G** or choose
**Generate**. This field is required.

You get up to five **opportunities**. Each recalls something established in the
Campaign and suggests a concrete way it could meet the situation you described.
Fewer is normal, and none is possible when nothing fits well, in which case try
rewording your prompt.

The suggestions favor ways for your players to discover and start using an old
element themselves. A returning element might gain **new meaning** (later events
change what it was) or **new utility** (the players can use it as a tool), and
callbacks that are purely emotional are valid too. TableSage separates what
happened in play from what it is proposing, so you can tell fact from suggestion.

Press **Ctrl+S** or choose **Save Markdown…** to keep the result as a Markdown
file. You can revise your prompt and generate again as often as you like; each
result replaces the last, and nothing is kept unless you save it.

If your Campaign is too large for the model to read in one pass, TableSage says so
instead of producing a partial result.
