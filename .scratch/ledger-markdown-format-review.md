# Ledger Markdown format review — Brandonsford 001

Reviewing `.tablesage/campaigns/Brandonsford/001/ledger.md` (49 entries, 201 lines), produced by
`Ledger.to_markdown()` in `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py:128`.

The content is good. The rendering is what makes it a slog.

## What is actually repetitive

Measured on this ledger:

| Repetition | Count |
|---|---|
| Entries whose heading ends `— Game Master` | 30 / 49 |
| Entries that spend 3 lines on 1 sentence (heading + `**Entity:**` + payload) | 21 |
| Entries that spend 2 lines on 1 sentence | 27 |
| Characters spent purely on field labels (`**Statement:**`, `**Entity:**`, …) | 719 |

Three structural causes:

1. **Double labelling.** `**Speech — Game Master**` followed by `- **Statement:**` says "speech" twice.
   The type word and the payload label are the same information.
2. **`source` is near-constant.** The GM sources 30 of 49 entries, so the heading's most prominent
   token carries almost no information — while `entity` (Lady Hilda, Farmer Gill, Drop Dead Ned),
   which is what a reader actually tracks, is demoted to a sub-bullet.
3. **No scene structure.** One flat 1–49 list across five location cuts (Clumsy Fox → river →
   Gill's farm → back to the Fox → Golden Egg). The reader has no landmarks, and the ledger has to
   burn narration entries on "Back at the Clumsy Fox…" (entries 27, 43) purely to re-orient.

Two content-level issues that are *not* the renderer's fault, noted here because they show up
in the same reading:

- Character introductions restate the name: `**Waymon Tisdale:** Waymon Tisdale, a Dagonite assassin.`
- Two Narration entries carry a **player name** as `source` (`rich gredzinski`, entries 8 and 22)
  where every other entry carries a role. `source` is specified as "the role or character…, not the
  human player at the table" (`canonical_ledger_format_v3.md` §3).

## Tier 1 — renderer only (no LLM re-run; re-renders every existing ledger)

Rules, all deterministic:

- One entry = one line. Fold the payload onto the heading line; drop `**Entity:**`/`**Statement:**`/
  `**Action:**`/`**Sentiment:**` labels entirely — the type already fixes what the payload means.
- Lead with `entity`, not `source`. For Speech/Action/Expression, show `entity` only; `source` is
  suppressed. Verified safe on this ledger: **no** entity-bearing entry has a `source` that is
  neither the entity nor the Game Master, so nothing is lost. (Caveat: this is the only `ledger.json`
  on disk — 002 has none yet.)
- Narration has no entity, so it is the one place `source` still shows. **This is where Tier 1 and
  Tier 2 interact.** The samples below print `*(established by rich gredzinski)*` only for non-GM
  sources — which means string-matching `"Game Master"`, and `source` is explicitly unvalidated
  (`generate_ledger.md`: "A regular `source` may be any non-empty string and is not checked against
  the Session role list"). One run that emits `GM` or `game master` would stamp an attribution on
  all nine narrations — the exact noise being removed. So: once Tier 2 lands, narration `source`
  can be dropped unconditionally with no string match anywhere, and the player-name leak surfaces
  as a generation warning instead of as renderer output. Until then, the sample's behaviour is a
  stopgap, not a durable rule.
- Speech stays **unquoted**. `generate_ledger.md` is right that the schema promises no verbatim
  wording, and the data proves it: entry 14 has stage direction baked into the statement.
- Speech's `**Name:**` form survives the content better than Action/Expression's `**Name** —`:
  the payloads are already dense in em dashes (entries 1, 2, 4, 23), so the dash separator competes
  with the prose. Worth weighing if you pick a dash-heavy form.
- Question compresses to one Q→A line; unresolved gets a trailing `*unresolved*`.
- Move `Session ID` / `Ledger format` to a small footer. They are machine metadata sitting in the
  first thing a human reads.

Two variants below, rendered from the real ledger. Same rules; they differ only in whether the
type is a word or a shape.

### Variant A — compact typed

*(entries 1–8)*

1. *narration* · Brandonsford is a quiet little town on the edge of the wilderness: thatched-roof stone cottages, two big plaster-and-timber inns facing each other — the Clumsy Fox Tavern and the Golden Egg Tavern — and an ancient small stone wall around the town. There are no guards or proper law enforcement; the town is protected by a rotating group of able-bodied men on night watch.

2. *speech* · **Night watchman** — Halt — who goes there, and what business do you have in this town?

3. *speech* · **Sir Phidipaldi** — We are ancient travelers who claim the sacred law of Zeus for hospitality.

4. *speech* · **Night watchman** — You're suspicious, and we don't get many visitors, but night is falling — better come in. There are two inns: the Clumsy Fox, which is busy, warm and cozy, and the Golden Egg across the street, which has far fewer people.

5. *narration* · Down the street are a general store, a smith, a small church, and an alchemist shop; there is also a farm on the edge of town.

6. *action* · **Dr Uriah** — Before going into town, goes to the river and casts speak with aquatic animals, seeking an aquatic creature with an opinion on the town's inns. He meets a frog.

7. *speech* · **Reginald** — The frog doesn't know which tavern is better, but warns that at night a little creature called a Clurichen comes from the river banks into town. He's a trickster and up to no good — wherever he goes, you want to stay away from.

8. *narration* · The frog is named Reginald, and Dr Uriah has befriended him. *(established by rich gredzinski)*


*(entries 20–24)*

20. *narration* · The scene shifts to the farm on the edge of town, where Dunk approaches as the sun sets. Farmer Gill sits on his porch chewing straw and packing a pipe.

21. *speech* · **Farmer Gill** — Remarks that Dunk would be amazing at farm work, and offers to sell him his mule for 100 gold so he could start his own farm.

22. *narration* · Farmer Gill's mule — a shabby, low-rent creature — is named Seamus. *(established by rich gredzinski)*

23. *speech* · **Farmer Gill** — The big work needed is killing the dragon outside town. Long ago, Sir Brandon lived right around this town; he and his friends ventured into the woods and killed the dragon that had been terrorizing the town. A fairy in the woods gave Brandon a magic sword, and that sword killed the dragon. He was knighted and the town was named Brandonsford after him, but he didn't stay, and he has since died. That dragon was truly dead — they dragged it through town and ripped it apart hundreds of years ago — so this must be a different dragon. Gill himself saw the dragon; it saw him and wanted nothing to do with him, and he was scared. He sent his boys off after it — they're out trying to kill it right now, and he's sure they'll manage.

24. *question* · **rich gredzinski:** How many sons did Farmer Gill send after the dragon? → **jason beaumont:** Three — Gill insists they'll be fine.


*(entries 27–35)*

27. *narration* · Back at the Clumsy Fox, Sir Phidipaldi has finished talking to Lady Hilda and approaches Eric the Reeve, a portly man with big mutton chops.

28. *expression* · **Eric the Reeve** — Has purple rings around his eyes and looks visibly stressed.

29. *speech* · **Eric the Reeve** — He has a lot of problems — first of all, the dragon. He will pay 1000 gold to whoever kills the dragon and drags its body into town. A woodsman named George, who lives a couple houses down and might show up tonight, encountered the dragon and lost his arm to it. George says it's a black dragon, not a big one. George is capable but one-armed, so he can't kill it himself.

30. *speech* · **Sir Phidipaldi** — Committing a faux pas, he lectures Eric that there is no such thing as black dragons — that verified sightings are actually illusions created by Clurichens, small river creatures that trick people and sometimes steal their limbs.

31. *expression* · **Dr Uriah** — Checking his lore, knows Sir Phidipaldi has it wrong — and that Eric the Reeve knows it too.

32. *expression* · **Eric the Reeve** — Looks offended.

33. *speech* · **Eric the Reeve** — He's known George all his life — there's no way he lied. How would a Clurichen take his arm? George doesn't even know where his arm is.

34. *action* · **Sir Phidipaldi** — Takes off his glove, slaps Eric the Reeve across the face with it, and challenges him to a duel at dawn.

35. *expression* · **Eric the Reeve** — Visibly flustered and at a loss for words, stammering that Sir Phidipaldi is obviously more skilled in adventure than he is.


*(entries 43–49)*

43. *narration* · Back at the Clumsy Fox, the altercation between Eric the Reeve and Sir Phidipaldi grows more and more heated.

44. *speech* · **Bentley** — Putting a hand on Sir Phidipaldi's shoulder: he wants no fighting in here. Phidipaldi's friends can stay, but since he caused trouble, he'll have to spend the night across the street at the Golden Egg. His drink is on the house.

45. *action* · **Bentley** — Escorts Sir Phidipaldi out of the Clumsy Fox, plate mail clanking, as the knight blusters about how Zeus's law of courtesy is no longer honored and doom is foretold for the tavern.

46. *narration* · The Golden Egg Tavern is the opposite of the Clumsy Fox: nobody there, no music, no food — just Quinn, the white-bearded, bony, odd-looking owner tending bar, who is almost startled that anyone came in.

47. *speech* · **Quinn** — Introduces himself as Quinn, the owner, and immediately charges 10 silver pieces for an ale — three times the price across the street — which turns out to be completely watered down. He apologizes: no matter how much good stuff he gets in, it's gone the next morning. He'll go to bed with a fully stocked bar, and by morning half the glasses are empty or knocked over. He believes Bentley steals it at night — that's why the Fox Tail brew is so popular.

48. *speech* · **Quinn** — Offers 100 gold if Sir Phidipaldi helps him get back at Bentley. Since no real shipments have arrived in a while, his plan: stage a fake shipment — fill bottles with water, hide some downstairs, and make a big show of delivering ale — then watch to see what's really going on.

49. *speech* · **Sir Phidipaldi** — Delighted to find courtesy is not lost in this town, he declares his shared hatred for the tavern across the street and agrees to the plan: Quinn should bring the bottles up, they'll fill them with water, and Phidipaldi will make a big show of coming in and delivering the ale.


*(synthetic Correction, for shape only)*

99. **⚠ correction** · Game Master: The smith's name is Warwick, not Warlock as stated earlier.


### Variant B — typographic

*(entries 1–8)*

Brandonsford is a quiet little town on the edge of the wilderness: thatched-roof stone cottages, two big plaster-and-timber inns facing each other — the Clumsy Fox Tavern and the Golden Egg Tavern — and an ancient small stone wall around the town. There are no guards or proper law enforcement; the town is protected by a rotating group of able-bodied men on night watch.

**Night watchman:** Halt — who goes there, and what business do you have in this town?

**Sir Phidipaldi:** We are ancient travelers who claim the sacred law of Zeus for hospitality.

**Night watchman:** You're suspicious, and we don't get many visitors, but night is falling — better come in. There are two inns: the Clumsy Fox, which is busy, warm and cozy, and the Golden Egg across the street, which has far fewer people.

Down the street are a general store, a smith, a small church, and an alchemist shop; there is also a farm on the edge of town.

**Dr Uriah** — Before going into town, goes to the river and casts speak with aquatic animals, seeking an aquatic creature with an opinion on the town's inns. He meets a frog.

**Reginald:** The frog doesn't know which tavern is better, but warns that at night a little creature called a Clurichen comes from the river banks into town. He's a trickster and up to no good — wherever he goes, you want to stay away from.

The frog is named Reginald, and Dr Uriah has befriended him. *— rich gredzinski*


*(entries 20–24)*

The scene shifts to the farm on the edge of town, where Dunk approaches as the sun sets. Farmer Gill sits on his porch chewing straw and packing a pipe.

**Farmer Gill:** Remarks that Dunk would be amazing at farm work, and offers to sell him his mule for 100 gold so he could start his own farm.

Farmer Gill's mule — a shabby, low-rent creature — is named Seamus. *— rich gredzinski*

**Farmer Gill:** The big work needed is killing the dragon outside town. Long ago, Sir Brandon lived right around this town; he and his friends ventured into the woods and killed the dragon that had been terrorizing the town. A fairy in the woods gave Brandon a magic sword, and that sword killed the dragon. He was knighted and the town was named Brandonsford after him, but he didn't stay, and he has since died. That dragon was truly dead — they dragged it through town and ripped it apart hundreds of years ago — so this must be a different dragon. Gill himself saw the dragon; it saw him and wanted nothing to do with him, and he was scared. He sent his boys off after it — they're out trying to kill it right now, and he's sure they'll manage.

**?** rich gredzinski: How many sons did Farmer Gill send after the dragon?
**A** jason beaumont: Three — Gill insists they'll be fine.


*(entries 27–35)*

Back at the Clumsy Fox, Sir Phidipaldi has finished talking to Lady Hilda and approaches Eric the Reeve, a portly man with big mutton chops.

**Eric the Reeve** — *Has purple rings around his eyes and looks visibly stressed.*

**Eric the Reeve:** He has a lot of problems — first of all, the dragon. He will pay 1000 gold to whoever kills the dragon and drags its body into town. A woodsman named George, who lives a couple houses down and might show up tonight, encountered the dragon and lost his arm to it. George says it's a black dragon, not a big one. George is capable but one-armed, so he can't kill it himself.

**Sir Phidipaldi:** Committing a faux pas, he lectures Eric that there is no such thing as black dragons — that verified sightings are actually illusions created by Clurichens, small river creatures that trick people and sometimes steal their limbs.

**Dr Uriah** — *Checking his lore, knows Sir Phidipaldi has it wrong — and that Eric the Reeve knows it too.*

**Eric the Reeve** — *Looks offended.*

**Eric the Reeve:** He's known George all his life — there's no way he lied. How would a Clurichen take his arm? George doesn't even know where his arm is.

**Sir Phidipaldi** — Takes off his glove, slaps Eric the Reeve across the face with it, and challenges him to a duel at dawn.

**Eric the Reeve** — *Visibly flustered and at a loss for words, stammering that Sir Phidipaldi is obviously more skilled in adventure than he is.*


*(entries 43–49)*

Back at the Clumsy Fox, the altercation between Eric the Reeve and Sir Phidipaldi grows more and more heated.

**Bentley:** Putting a hand on Sir Phidipaldi's shoulder: he wants no fighting in here. Phidipaldi's friends can stay, but since he caused trouble, he'll have to spend the night across the street at the Golden Egg. His drink is on the house.

**Bentley** — Escorts Sir Phidipaldi out of the Clumsy Fox, plate mail clanking, as the knight blusters about how Zeus's law of courtesy is no longer honored and doom is foretold for the tavern.

The Golden Egg Tavern is the opposite of the Clumsy Fox: nobody there, no music, no food — just Quinn, the white-bearded, bony, odd-looking owner tending bar, who is almost startled that anyone came in.

**Quinn:** Introduces himself as Quinn, the owner, and immediately charges 10 silver pieces for an ale — three times the price across the street — which turns out to be completely watered down. He apologizes: no matter how much good stuff he gets in, it's gone the next morning. He'll go to bed with a fully stocked bar, and by morning half the glasses are empty or knocked over. He believes Bentley steals it at night — that's why the Fox Tail brew is so popular.

**Quinn:** Offers 100 gold if Sir Phidipaldi helps him get back at Bentley. Since no real shipments have arrived in a while, his plan: stage a fake shipment — fill bottles with water, hide some downstairs, and make a big show of delivering ale — then watch to see what's really going on.

**Sir Phidipaldi:** Delighted to find courtesy is not lost in this town, he declares his shared hatred for the tavern across the street and agrees to the plan: Quinn should bring the bottles up, they'll fill them with water, and Phidipaldi will make a big show of coming in and delivering the ale.


*(synthetic Correction, for shape only)*

> **Correction (Game Master):** The smith's name is Warwick, not Warlock as stated earlier.

Current format, same entries, for comparison:

### Current format

*(entries 1–8)*

1. **Narration — Game Master**
   Brandonsford is a quiet little town on the edge of the wilderness: thatched-roof stone cottages, two big plaster-and-timber inns facing each other — the Clumsy Fox Tavern and the Golden Egg Tavern — and an ancient small stone wall around the town. There are no guards or proper law enforcement; the town is protected by a rotating group of able-bodied men on night watch.

2. **Speech — Game Master**
   - **Entity:** Night watchman
   - **Statement:** Halt — who goes there, and what business do you have in this town?

3. **Speech — Sir Phidipaldi**
   - **Statement:** We are ancient travelers who claim the sacred law of Zeus for hospitality.

4. **Speech — Game Master**
   - **Entity:** Night watchman
   - **Statement:** You're suspicious, and we don't get many visitors, but night is falling — better come in. There are two inns: the Clumsy Fox, which is busy, warm and cozy, and the Golden Egg across the street, which has far fewer people.

5. **Narration — Game Master**
   Down the street are a general store, a smith, a small church, and an alchemist shop; there is also a farm on the edge of town.

6. **Action — Dr Uriah**
   - **Action:** Before going into town, goes to the river and casts speak with aquatic animals, seeking an aquatic creature with an opinion on the town's inns. He meets a frog.

7. **Speech — Game Master**
   - **Entity:** Reginald
   - **Statement:** The frog doesn't know which tavern is better, but warns that at night a little creature called a Clurichen comes from the river banks into town. He's a trickster and up to no good — wherever he goes, you want to stay away from.

8. **Narration — rich gredzinski**
   The frog is named Reginald, and Dr Uriah has befriended him.


*(entries 20–24)*

20. **Narration — Game Master**
   The scene shifts to the farm on the edge of town, where Dunk approaches as the sun sets. Farmer Gill sits on his porch chewing straw and packing a pipe.

21. **Speech — Game Master**
   - **Entity:** Farmer Gill
   - **Statement:** Remarks that Dunk would be amazing at farm work, and offers to sell him his mule for 100 gold so he could start his own farm.

22. **Narration — rich gredzinski**
   Farmer Gill's mule — a shabby, low-rent creature — is named Seamus.

23. **Speech — Game Master**
   - **Entity:** Farmer Gill
   - **Statement:** The big work needed is killing the dragon outside town. Long ago, Sir Brandon lived right around this town; he and his friends ventured into the woods and killed the dragon that had been terrorizing the town. A fairy in the woods gave Brandon a magic sword, and that sword killed the dragon. He was knighted and the town was named Brandonsford after him, but he didn't stay, and he has since died. That dragon was truly dead — they dragged it through town and ripped it apart hundreds of years ago — so this must be a different dragon. Gill himself saw the dragon; it saw him and wanted nothing to do with him, and he was scared. He sent his boys off after it — they're out trying to kill it right now, and he's sure they'll manage.

24. **Question**
   - **Asked by:** rich gredzinski
   - **Question:** How many sons did Farmer Gill send after the dragon?
   - **Resolved by:** jason beaumont
   - **Answer:** Three — Gill insists they'll be fine.


*(entries 27–35)*

27. **Narration — Game Master**
   Back at the Clumsy Fox, Sir Phidipaldi has finished talking to Lady Hilda and approaches Eric the Reeve, a portly man with big mutton chops.

28. **Expression — Game Master**
   - **Entity:** Eric the Reeve
   - **Sentiment:** Has purple rings around his eyes and looks visibly stressed.

29. **Speech — Game Master**
   - **Entity:** Eric the Reeve
   - **Statement:** He has a lot of problems — first of all, the dragon. He will pay 1000 gold to whoever kills the dragon and drags its body into town. A woodsman named George, who lives a couple houses down and might show up tonight, encountered the dragon and lost his arm to it. George says it's a black dragon, not a big one. George is capable but one-armed, so he can't kill it himself.

30. **Speech — Sir Phidipaldi**
   - **Statement:** Committing a faux pas, he lectures Eric that there is no such thing as black dragons — that verified sightings are actually illusions created by Clurichens, small river creatures that trick people and sometimes steal their limbs.

31. **Expression — Dr Uriah**
   - **Sentiment:** Checking his lore, knows Sir Phidipaldi has it wrong — and that Eric the Reeve knows it too.

32. **Expression — Game Master**
   - **Entity:** Eric the Reeve
   - **Sentiment:** Looks offended.

33. **Speech — Game Master**
   - **Entity:** Eric the Reeve
   - **Statement:** He's known George all his life — there's no way he lied. How would a Clurichen take his arm? George doesn't even know where his arm is.

34. **Action — Sir Phidipaldi**
   - **Action:** Takes off his glove, slaps Eric the Reeve across the face with it, and challenges him to a duel at dawn.

35. **Expression — Game Master**
   - **Entity:** Eric the Reeve
   - **Sentiment:** Visibly flustered and at a loss for words, stammering that Sir Phidipaldi is obviously more skilled in adventure than he is.


*(entries 43–49)*

43. **Narration — Game Master**
   Back at the Clumsy Fox, the altercation between Eric the Reeve and Sir Phidipaldi grows more and more heated.

44. **Speech — Game Master**
   - **Entity:** Bentley
   - **Statement:** Putting a hand on Sir Phidipaldi's shoulder: he wants no fighting in here. Phidipaldi's friends can stay, but since he caused trouble, he'll have to spend the night across the street at the Golden Egg. His drink is on the house.

45. **Action — Game Master**
   - **Entity:** Bentley
   - **Action:** Escorts Sir Phidipaldi out of the Clumsy Fox, plate mail clanking, as the knight blusters about how Zeus's law of courtesy is no longer honored and doom is foretold for the tavern.

46. **Narration — Game Master**
   The Golden Egg Tavern is the opposite of the Clumsy Fox: nobody there, no music, no food — just Quinn, the white-bearded, bony, odd-looking owner tending bar, who is almost startled that anyone came in.

47. **Speech — Game Master**
   - **Entity:** Quinn
   - **Statement:** Introduces himself as Quinn, the owner, and immediately charges 10 silver pieces for an ale — three times the price across the street — which turns out to be completely watered down. He apologizes: no matter how much good stuff he gets in, it's gone the next morning. He'll go to bed with a fully stocked bar, and by morning half the glasses are empty or knocked over. He believes Bentley steals it at night — that's why the Fox Tail brew is so popular.

48. **Speech — Game Master**
   - **Entity:** Quinn
   - **Statement:** Offers 100 gold if Sir Phidipaldi helps him get back at Bentley. Since no real shipments have arrived in a while, his plan: stage a fake shipment — fill bottles with water, hide some downstairs, and make a big show of delivering ale — then watch to see what's really going on.

49. **Speech — Sir Phidipaldi**
   - **Statement:** Delighted to find courtesy is not lost in this town, he declares his shared hatred for the tavern across the street and agrees to the plan: Quinn should bring the bottles up, they'll fill them with water, and Phidipaldi will make a big show of coming in and delivering the ale.


*(synthetic Correction, for shape only)*

99. **CORRECTION — Game Master**
   > The smith's name is Warwick, not Warlock as stated earlier.


## Tier 2 — prompt only (needs regeneration, no code change)

- Character Introduction `description` should not restate `character`. Prompt it to describe, not
  re-announce: `**Waymon Tisdale** — a Dagonite assassin.`
- `source` on Narration must be a role, never a player name (entries 8, 22). Today this is a
  *warning-free* mistake: `generate_ledger.py:269` only checks introduced characters and Question
  askers against the roster; regular `source` is deliberately unchecked. Tightening the prompt is the
  cheap fix; adding a regular-`source`-not-in-known-roles warning to `_introduction_warning_count`'s
  sibling would make it self-correcting.

## Tier 3 — schema v4: scenes (the biggest readability win, and the only one you cannot render your way to)

The renderer cannot infer scene boundaries — that is interpretation, and `to_markdown()` is
committed to adding none. So this needs the LLM to emit them.

Of the two shapes, **a nullable `scene_break` title on the existing flat utterance list is the right
one**, not `scenes: [{title, utterances: [...]}]`. Nesting utterances inside scenes is containment,
and containment is a deliberate v3 exclusion: `generate_ledger.md` says "The Ledger has no time
offsets, sequence fields, stable entry IDs, containment, or transcript-source mappings", and
`canonical_ledger_format_v3.md`'s header records that v1's containment inheritance did not carry
forward. `scene_break` keeps array order authoritative, adds one optional field, and gives the
renderer everything it needs to emit headings.

What it buys, on this session:

- Five cuts between Clumsy Fox / river / Gill's farm / back to the Fox / Golden Egg become
  navigable headings and a table of contents.
- The re-orienting narrations at 27 and 43 ("Back at the Clumsy Fox…") stop being needed — that
  boilerplate exists *only* because the format has no place to say where we are.

Sketch, using Variant B inside scenes (scene titles illustrative — the LLM would supply them):

### Gill's farm, sunset

The scene shifts to the farm on the edge of town, where Dunk approaches as the sun sets. Farmer Gill sits on his porch chewing straw and packing a pipe.

**Farmer Gill:** Remarks that Dunk would be amazing at farm work, and offers to sell him his mule for 100 gold so he could start his own farm.

Farmer Gill's mule — a shabby, low-rent creature — is named Seamus. *— rich gredzinski*

**Farmer Gill:** The big work needed is killing the dragon outside town. Long ago, Sir Brandon lived right around this town; he and his friends ventured into the woods and killed the dragon that had been terrorizing the town. A fairy in the woods gave Brandon a magic sword, and that sword killed the dragon. He was knighted and the town was named Brandonsford after him, but he didn't stay, and he has since died. That dragon was truly dead — they dragged it through town and ripped it apart hundreds of years ago — so this must be a different dragon. Gill himself saw the dragon; it saw him and wanted nothing to do with him, and he was scared. He sent his boys off after it — they're out trying to kill it right now, and he's sure they'll manage.

**?** rich gredzinski: How many sons did Farmer Gill send after the dragon?

**A** jason beaumont: Three — Gill insists they'll be fine.

**Dunk:** He's done a little farm work in his time, and doesn't really know what he is — when he was just a little dude, he was sent out of his village.

**Dunk** — Asks to sleep in Gill's barn tonight while he thinks things over; Gill agrees and fetches drinks from his still so the two can sit out on the porch.

### The Clumsy Fox — Eric the Reeve

Sir Phidipaldi has finished talking to Lady Hilda and approaches Eric the Reeve, a portly man with big mutton chops.

**Eric the Reeve** — *Has purple rings around his eyes and looks visibly stressed.*

**Eric the Reeve:** He has a lot of problems — first of all, the dragon. He will pay 1000 gold to whoever kills the dragon and drags its body into town. A woodsman named George, who lives a couple houses down and might show up tonight, encountered the dragon and lost his arm to it. George says it's a black dragon, not a big one. George is capable but one-armed, so he can't kill it himself.

**Sir Phidipaldi:** Committing a faux pas, he lectures Eric that there is no such thing as black dragons — that verified sightings are actually illusions created by Clurichens, small river creatures that trick people and sometimes steal their limbs.

**Dr Uriah** — *Checking his lore, knows Sir Phidipaldi has it wrong — and that Eric the Reeve knows it too.*

**Eric the Reeve** — *Looks offended.*

**Eric the Reeve:** He's known George all his life — there's no way he lied. How would a Clurichen take his arm? George doesn't even know where his arm is.

**Sir Phidipaldi** — Takes off his glove, slaps Eric the Reeve across the face with it, and challenges him to a duel at dawn.

**Eric the Reeve** — *Visibly flustered and at a loss for words, stammering that Sir Phidipaldi is obviously more skilled in adventure than he is.*


## Collateral for any of this

A renderer change is not just `to_markdown()`:

- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py:128-196`
  (`to_markdown` / `_render_markdown_utterance`).
- `.documentation/generate_ledger.md` — the "Artifact and UI Behavior" bullet specifies the current
  output shape verbatim ("type/source headings with payload labels", "Speech uses an unquoted
  `Statement` label"), and the "Acceptance Coverage" renderer bullet lists the current features.
- `packages/tablesage-application/tests/session_pipeline/test_generate_ledger.py:115` and `:401-415`
  assert on rendered text.
- `.documentation/canonical_ledger_format_v3.md` and the generation prompt, for Tier 3 only.

Nothing renders `ledger.md` inside the TUI — there is no Textual `Markdown` widget in
`apps/tablesage-tui/src`; it is written to disk and exported. So typography is only constrained by
whatever the user reads it in (editor / GitHub), and blockquotes, bold and italics are all safe.

Existing ledgers do not need regeneration for Tier 1: `ledger.md` is derived, and
`application.py:454` already re-renders it from `ledger.json` on export.

## Recommendation

**Variant B, with entry numbers kept.** The complaint was repetitiveness, and Variant A still prints
a type word 49 times — the same kind of thing. Numbering is orthogonal to typography: it costs one
token per line and makes review possible ("fix 31"), so keep it in B even though the sample above
drops it. Then Tier 2 (prompt), which makes B's narration rule honest. Then `scene_break`.

## Open decisions

1. **Variant A or B?** (recommendation above: B) A keeps a type word (`*speech*`, `*action*`) — scannable, still slightly
   repetitive. B drops type words and lets form carry the type (`**Name:**` = speech,
   `**Name** —` = action, `**Name** — *italic*` = expression, bare paragraph = narration) — reads
   like a play script but Action vs. Expression is a subtle italic cue.
2. **Keep entry numbers?** (recommendation: yes, in either variant) They are handy for review but
   the format has no stable entry IDs, so a number is only valid until the next regeneration.
3. **How far to go on Tier 3** — `scene_break` on the flat list (recommended, and arguably still
   v3-compatible as an optional field) vs. a full v4 with a `scenes` level.
