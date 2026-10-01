# Prepare the Next Session

Turn campaign history into a recap to read at the table and possible ways to bring established elements back into play. Two tools on Campaign Detail read the **scene breakdowns** of your earlier Sessions (the scene-by-scene record produced during processing):

- **Create Previously On** helps you pick the scenes worth recalling and writes a short "previously on…" recap you can read to the table.
- **Generate Opportunities** suggests established campaign elements that could return in a useful or surprising way in the Session you have in mind.

Both send campaign text to an LLM, which reads the history and writes the results. Choose that model in [Update Your Settings](settings.md); see [Privacy and Data Handling](../reference/privacy.md) for what is sent. Neither saves anything inside TableSage; what you produce is a Markdown file you keep. Save it as a `.md` file outside the workspace's `campaigns/` folder, which TableSage manages itself.

## What You Need First

You need a Campaign with at least one processed Session, plus some idea of the situation you expect next. Preparation tools read Sessions in number order and ignore the highest-numbered Session if it has no imported audio yet. Every remaining Session must have a **current, complete scene breakdown**. If any doesn't qualify, TableSage stops and lists which Sessions have a problem and why.

Session dates do not determine this order; they are used separately to [choose the prior recap in a session summary](../concepts/sessions.md#how-the-prior-recap-is-chosen). If you add older recordings later, check the starting situation before continuing.

1. From the Welcome screen, press **C** and open your Campaign.
2. If the history needs refreshing, open **Other actions** (**?**) and choose **Regenerate All Outputs** (**O**); see [Regenerate Every Session in a Campaign](review-and-export.md#regenerate-every-session-in-a-campaign).
3. Complete processing for any Sessions skipped because their transcript reviews are incomplete or out of date, then refresh again. If a listed Session has no recording at all (for example, a game that was never recorded), delete it; Regenerate All Outputs cannot build anything for it.
4. Choose either preparation tool from **Other actions**. You can use one or both; neither depends on the other's result.

For example, if next time the party will return to the harbor to claim a promised permit, focus your notes on that return. The recap can remind players of the bargain, while Opportunities can suggest ways earlier people, objects, or commitments might become useful there.

## Create Previously On

Choose **Create Previously On** (**V**). The tool works in two stages.

**1. Say what is coming.** TableSage reads the Campaign and shows:

- **Starting situation**, pre-filled from where the highest-numbered Session included in the history ended. Edit it to match how you actually plan to open.
- **What might happen next Session?** Your notes on where play may go.
- **Campaign ingredients**: up to five candidates in each of *People & Factions*, *Threads & Commitments*, *Active Pressures*, and *Places & Objects*, each with its current state. Focus one to read the scenes it comes from. Press **Space** or **Enter** to select the ones that matter.

Select at least one ingredient or write some notes, then choose **Continue** or press **C** with focus outside a text field. If a suggestion is wrong, correct it in your notes. For the harbor example, select the official and the permit commitment, and explain that the party intends to collect what was promised.

**2. Choose the scenes.** TableSage recommends scenes from across the Campaign, starred **★ Scout**, with a rationale for each that only you see. The list shows every Session and its scenes. Press **Space** or **Enter** to add or remove a scene, or to expand a Session, and focus a scene to read its full record. You may choose any scenes, not only the recommended ones.

Choose scenes that give players the context they need for the opening: the original bargain, any changed conditions, and where the party ended last time. Choose **Continue** (**C**), pick a destination, and TableSage writes a concise recap of only the scenes you chose. The suggested filename names the Campaign and the next session number. If the file already exists, you are asked to replace it, and the old file stays intact until the new one is written. If saving fails, fix the cause and choose **Retry Save**.

**Back** returns to stage one. **Exit** (or **Esc**) asks before discarding your inputs, because this tool does not keep drafts.

## Generate Opportunities

Choose **Generate Opportunities** (**Y**). TableSage shows where the Campaign currently stands (its ending situation) and asks **What might happen next Session?** Describe the situation you expect, move focus out of the prompt with **Tab**, and press **G** or choose **Generate**. This field is required. A useful prompt gives a concrete situation, such as “The party returns to the harbor to claim the permit. They may need to persuade the official or find another route out.”

You get up to five **opportunities**. Each recalls something established in the Campaign and suggests a concrete way it could meet the situation you described. Fewer is normal, and none is possible when nothing fits well, in which case try rewording your prompt.

The suggestions favor ways for your players to discover and start using an old element themselves. A returning element might gain **new meaning** (later events change what it was) or **new utility** (the players can use it as a tool), and callbacks that are purely emotional are valid too. TableSage separates what happened in play from what it is proposing, so you can tell fact from suggestion.

Press **C** outside an editable field or choose **Continue** to keep the result as a Markdown file. You can revise your prompt and generate again as often as you like; each result replaces the last, and nothing is kept unless you save it.

If your Campaign is too large for the model to read in one pass, TableSage says so instead of producing a partial result.

## Put the Preparation to Use

Open the saved Markdown files and read them before play. Check the Previously On recap against what your players should remember, and adapt it for your voice. Choose the opportunities that fit your game; proposed developments are possibilities for you to consider, not established campaign facts.

You are ready when you have a recap you can read and any opportunities you want to keep in your preparation notes. If a recap of only the latest Session is enough, [export its Recap Summary](review-and-export.md) instead. After the next game, [process its recording](process-session-returning-players.md), using the [new-player workflow](process-session-new-players.md) if someone without a usable voice print joins.
