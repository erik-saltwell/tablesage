# Overview

Extract and reconcile Opportunities: established openings for gaining a concrete advantage toward a goal, tracked through their lifecycle. Available openings must support a supplied open Goal. Retain ended entries so captured, lost and obsolete openings remain tracked. Return only this category. The characters need not have chosen to pursue an opening.

# Definitions

An **Opportunity** is an established opening that requires action by the party to secure an advantage toward an established goal, including by overcoming or bypassing a Goal Impediment. Both the opening and its potential advantage must be supported by play; possible usefulness alone is insufficient.

Each entry has nine properties:

- `id`: stable Opportunity identity. Keep prior `opportunity_<n>` IDs; use distinct temporary `opportunity_new_<n>` IDs for newly identified entries. Code assigns permanent IDs and rewrites parent references after validation.
- `parent_opportunity_id`: the ID of the immediate Opportunity whose advantage this opening helps secure, or `null` for a top-level opportunity. Children share the parent's goal link.
- `title`: a short, simple read-aloud title combining the established opening, the action needed and the potential advantage, in one sentence or, when one would be crowded, two short sentences.
- `opening`: the established person, item, offer, access or circumstance that creates the option.
- `action`: what the characters must do to secure its advantage, including consequential costs and requirements.
- `advantage`: what that action could make possible or improve toward the linked goal. Preserve uncertainty rather than guaranteeing success.
- `goal_id`: the permanent ID of the goal the opportunity helps achieve. Available entries require a supplied open Goal; ended entries retain their established goal link.
- `goal_impediment_title`: the exact title of an optional Goal Impediment affecting that same goal, or `null`. Available entries require a uniquely matching supplied anticipated or active impediment; ended entries preserve the established reference.
- `lifecycle`: `available` (still actionable), `captured` (the described advantage was secured), `lost` (the opening closed before its advantage was secured), or `obsolete` (changed circumstances removed its relevance, or a prior entry was misclassified).

Goals state desired outcomes. Impediments state established obstructions. Opportunities state actionable openings that improve the characters' chances. An acquired resource is not itself an uncompleted acquisition opportunity.

# Input Description

- `<scene_log>` supplies the complete current session's Events and Discoveries as evidence. Check both for openings and developments affecting them.
- `<previous_section>` contains only the immediately preceding session's Opportunities, or an empty array when there is no preceding session. Historical entries may be strings without links or separated text fields, or objects without lifecycle or hierarchy fields; reassess them against the current definition and supplied evidence rather than assuming a status. Carry every prior structured entry, including ended ones. Legacy strings that cannot be grounded to a goal do not qualify; never invent a link to preserve one.
- `<current_sections>` contains only current `goals` and `goal_impediments` (the obstacles). They supply the goals and permitted references. No other current Campaign Matters categories are supplied. Use the Scene Log and prior Opportunities as evidence of acquisition, recruitment or other changes affecting availability; do not require a separate New Assets list.
- `<attending_character_roles>` identifies the player characters.

# Process

1. Reconcile every prior entry, including ended ones, and discover candidates anywhere in the Scene Log. Silence alone does not close a supported available opening or reopen an ended one.
2. Qualify new candidates: require an established opening, an identifiable action and a concrete advantage toward a supplied goal. Include qualifying openings discovered and captured or lost within this session, even if they are no longer available at its end. Available entries require a supplied open Goal. An offer or reward without such a connection does not qualify; do not invent a goal to retain it. Do not reconstruct ended opportunities from routine past actions or acquired assets alone.
3. Identify top-level advantages and organize supporting openings beneath the Opportunity they enable. Retain a distinct actionable enabling opening as a child, rather than presenting every step as an independent top-level option. Ordinary requirements and payment terms stay within the relevant action. Assign each child its immediate parent and the same goal link; shared goals or subjects alone do not establish parenthood. Preserve prior IDs when reparenting carried entries. Assign temporary IDs to new entries and legacy entries that lack an ID.
4. Assign the most directly supported `goal_id` and optional `goal_impediment_title`. Available links must identify a current open goal and, when present, a uniquely matching anticipated or active impediment for that goal. Ended entries keep established historical links; do not reassign them to unrelated open goals or erase their impediment references merely because the targets ended or are absent from current selections.
5. Separate each retained entry into `opening`, `action` and `advantage`, then summarize them in a `title` and assign `lifecycle` from evidence. Preserve essential terms and uncertainty without repeating the same information in all three detailed text fields. For ended entries retain what the opening, required action and potential benefit were; lifecycle records the outcome without rewriting the entry as a new action. Supply a title for every entry, including carried entries that previously lacked one.
6. Retain captured, lost and obsolete entries instead of deleting them. Classify a formerly available opening as obsolete when its goal no longer remains open and no evidence establishes capture or loss. Preserve already established captured or lost outcomes when the goal later concludes. A mistaken prior entry becomes obsolete without invented success or loss.
7. Check every entry and every prior candidate against the final selection. Preserve distinct identities, parent links and lifecycle during shortening. Keep every prior permanent ID, including ended entries; never recycle an ID or silently merge distinct identified entries. Restore anything lost solely through compression or because another category mentions the same subject. Return all lifecycle values, without filtering, and only the final section, not the working inventory.

# Guidance

### Selecting openings

- Select specific advantages, not a directory of potentially useful people, shops or goods. Ordinary retail availability, general knowledge and routine services do not qualify without an established concrete application or specific offer that helps or helped a supplied goal; available entries require that goal to remain open. Ingrid's sleeping potion can enable access to Warwick; merely selling potions does not establish that opening. George's recommended account of his dragon encounter offers specific information for a dragon goal; someone merely knowing fairy tales does not establish what useful answer remains to obtain.
- Reconcile all supplied evidence for enabling resources. A retrievable sword reportedly able to kill the dragon can qualify even when retrieval is also a Goal and its location appears in Revelations. Keep the advantage visible here. Do not infer usefulness merely from an item's existence.
- The dragon's impenetrable scales are an Impediment; retrieving Brandon's sword is a reported countermeasure. Preserve the claim and doubts rather than making the sword the only possible solution. Obtaining the sword marks that retrieval opening `captured`, but does not by itself establish that the scales have been overcome.
- Obtaining Warwick's magical chain shirt is the top-level Opportunity toward the dragon goal. Using the sleeping potion and entering through the bedroom window are supporting child Opportunities of that acquisition. Supplying faun wine is a child of the potion opening when independently established. Do not leave these as competing top-level options. Paying Hilda's fee is a condition in her recruitment action, not a child Opportunity. A window establishes access, not entering unnoticed.
- Do not infer cooperation or leverage from gratitude, a stated favor, rescue or fear of exposure. A rescued person wanting to go home is not thereby available as an ally; saying they owe a favor does not establish what they will do. Require a supported benefit or cooperation.
- Once acquisition or recruitment is complete, retain the original opportunity as `captured`; the resulting resource or relationship may also qualify as a New Asset. Do not present the completed acquisition as still available. A new use qualifies only when play establishes a distinct opening and advantage toward a supplied open goal. Do not invent a use for an acquired asset.
- An opportunity can enable another opportunity along the way, but must still link to a goal and explain its contribution; available entries require an open goal. A bargain offering gold or a secret does not qualify solely because such rewards might be useful.

### Setting `title`

Write one short, simple sentence that makes the opening, the action and its potential advantage understandable together without reading the other fields. When one sentence would stack the mechanism, its condition and its benefit, use two short sentences instead, for example the claim and its source first, then what it would allow. Use natural sentence case and retain articles and other small words needed for readability. Usually aim for about 15–25 words in total, using more when necessary to preserve essential conditions, attribution or uncertainty. Do not merely repeat the opening or restate the goal. Describe an available option without recommending it, implying a commitment or guaranteeing success. Use only facts supported by the three detailed fields. For ended entries, summarize the original option without implying it is still available; preserve its recorded lifecycle.

- Good: "Father William says retrieving Sir Brandon's sword from the Barrow Mound could help slay the dragon."
- Good: "The innkeeper says the smugglers' tunnel starts behind her cellar wall. If the party clears it, they could reach the harbor unseen."
- Good: "Entering through Warwick's open bedroom window could provide access to his chain shirt."
- Avoid: "Sir Brandon's sword lies at the Barrow Mound." This omits the action and advantage.
- Avoid: "Retrieve the sword to guarantee victory over the dragon." This recommends an action and invents certainty.

### Read-aloud wording for `title`

The Session Summary shows `title` as a bullet under the heading "What could help". At the table, the Game Master reads the heading aloud and then each bullet, so write `title` to sound natural spoken right after that heading:

- Use sentence case: capitalize only the first word and proper nouns.
- Write a complete phrase that starts with a capital letter and makes sense on its own, without repeating the heading or continuing it as one sentence. Under "What could help", write "Lady Hilda will fight the dragon alongside the party if they pay her", not "What could help is Lady Hilda…".

Write each bullet so the Game Master understands it on first reading and can say it aloud without stumbling:

- Put the actor and the action early, so it is immediately clear who did, believes, offers or owes something. Use an active verb rather than a noun made from one: write "The miller agreed to give the party somewhere to stay if they investigate the disappearances", not "The party secured the miller's agreement to provide accommodation conditional upon their investigation of the disappearances".
- Use familiar verbs and everyday words: "pay" rather than "compensate", "if" rather than "conditional upon", "when" rather than "upon". Write "The party must pay the ferryman when they return with the recovered ledger", not "The party's obligation to compensate the ferryman becomes payable upon their successful return with the recovered ledger".
- When one sentence would stack several clauses, conditions or consequences, split it into two short sentences in the same bullet. Use a second sentence only when it makes the bullet easier to follow, never to add background or explanation. Avoid asides set off by commas, semicolons or brackets.
- Keep attribution and uncertainty beside the claim they qualify, and name the source first: write "The miller says the river may flood the ford", not "The river may flood the ford, according to the miller".
- Simpler wording must keep every name, amount, condition, cause, source and uncertainty, and keep individual characters distinct from the party. If a bullet is already clear, do not rewrite it.

### Setting `opening`

Lead with the person, item, offer or circumstance that creates or created the option. Include location when it enables access, and preserve the named owner or beneficiary. Avoid introductions such as "The party learned that", incidental appearance, equipment inventories, history and routes that do not affect the option.

- Good: "Warwick leaves his second-story bedroom window cracked open."
- Avoid: "The party could disguise themselves as maintenance workers to enter the smithy." This invents a tactic.

### Setting `action`

State the concrete action needed to secure the advantage. On a parent entry, summarize the established available approach and essential requirements so it remains useful when children are hidden; do not make readers reconstruct the action by following child IDs. On ended entries, preserve that original action rather than inventing a new remaining task. The action need not have been proposed during play, but established information must support it without adding capabilities, access, cooperation or outcomes. Describe an available option without recommending it or asserting that the party has committed to it.

Preserve established costs, requirements, restrictions, timing and payment recipients. Distinguish a recipe ingredient from a missing ingredient: knowing one is used does not establish that the brewer lacks it. Keep limitations such as diluted wine without inventing shortages or predicting failure.

- Good: "Retrieve Sir Brandon's sword from the Barrow Mound."
- Good: "Hire Lady Hilda for the dragon hunt on her offered payment terms."
- Avoid: "Kill the dragon and collect the bounty." This restates an outcome and reward without an enabling opening.

### Setting `advantage`

State the useful effect and how it advances the linked goal, directly or through another opening. Do not make players reconstruct the benefit from other categories, and do not repeat a whole chain when the immediate contribution is clear. Preserve attribution and uncertainty; never turn a possibility into a guaranteed outcome to make an entry fit.

- Good: "Father William says the sword can make killing the dragon possible, though its power remains untested."
- Good: "The window provides a way into the smithy to obtain the chain shirt."
- Avoid: "The Barrow Mound is marked on the map." This gives a location without an advantage.

### Setting links

Every entry must refer to a goal using its permanent `goal_<n>` ID. Available entries require a supplied open Goal. Ended entries may refer to concluded supplied goals or preserve a goal ID present in prior structured Opportunities when current Goals omit it. Link the most directly supported goal rather than duplicating the same opening for each related goal. An intention to exploit the opening is not required; an established goal that benefits or benefited from it is required. Exclude entries with no supported goal link, including historical entries previously retained solely as offers. Never infer a generic wealth or information goal from a reward.

The impediment link is optional and supplements the goal link. For available entries, use `null` when no supplied impediment matches; otherwise copy the exact title of one uniquely identifiable anticipated or active impediment whose `goal_ids` includes the chosen `goal_id`. A shared subject alone does not establish that the opening addresses the obstruction. Reassess available references each session; do not carry a stale title forward when the current impediment has changed. Ended entries may link a concluded supplied impediment or preserve the exact goal/title pair from prior structured Opportunities when its target has changed or is absent. Do not invent a historical reference or combine unrelated prior links.

### Setting `id` and `parent_opportunity_id`

Preserve the permanent ID of every prior identified entry across changes to its wording, parent, terms or lifecycle. Give new entries distinct `opportunity_new_<n>` IDs, including legacy entries that lack IDs. Use the same temporary ID when another entry references a new parent. Code assigns permanent IDs after the highest prior permanent ID and rewrites all parent references. Do not assign an arbitrary permanent ID to a new entry or omit a prior permanent ID. Historical entries remain unmodified in storage.

A parent groups the concrete advantage its children help secure. Use the immediate parent rather than attaching every descendant directly to the root. All linked entries must appear in the response and share a `goal_id`. No self-parent links, cycles or dangling parents are allowed. Top-level entries have `parent_opportunity_id: null`; consumers can select only those entries without changing the stored hierarchy.

Example: obtaining the chain shirt is a root; the window and sleeping potion are children of that root; supplying faun wine is a child of the potion. Brandon's sword remains a separate root even though it also advances the dragon goal. Do not create an umbrella "kill the dragon" Opportunity merely to group all openings for that goal. Do not invent a supporting step, parent benefit or dependency that play did not establish. A child is an actionable opening with a supported advantage, not an arbitrary task added to a checklist.

Keep all entries in the response, including children and ended parents. A child retains its own lifecycle. Supplying wine can be captured while the potion and shirt acquisition remain available. A child's completion does not automatically capture its parent; judge each entry's described advantage separately. Likewise, a parent concluding does not prove every alternative child was used or captured: reassess each child from evidence, marking an unused opening obsolete if it no longer has a relevant advantage. Keep established parent links on ended entries to preserve their identity.

### Setting `lifecycle`

- `available`: the party can still act to secure the advantage, and the linked goal remains open. Merely finding the opening, choosing it, negotiating or making an incomplete or unsuccessful attempt does not capture it. Silence, leaving the location or postponing action does not by itself close it.
- `captured`: evidence establishes that the party secured the advantage the entry describes. Retrieving the sword captures the retrieval opportunity; securing Hilda's agreement captures the recruitment opportunity. The linked goal need not be achieved, and the underlying impediment need not be overcome. An untested claim about the sword remains uncertain after acquisition.
- `lost`: the opening was exhausted, withdrawn, expired or otherwise closed before the described advantage was secured. Do not infer a deadline or closure from silence or an unsuccessful attempt that leaves the opening available.
- `obsolete`: changed circumstances remove the opening's relevance, including a concluded goal or an independently overcome obstruction leaving no remaining advantage. Use this for a misclassified prior structured entry, not as a way to invent a new opportunity.

Judge the specific advantage, not how much activity occurred. Using a repeatable opening once does not necessarily exhaust it: access that remains useful and available can stay `available`. A one-time acquisition or agreement is `captured` when secured even if the resulting asset remains useful. Do not reopen a captured acquisition merely because the asset can be used again, or merely because it is later lost; a distinct new opening needs its own evidence.

Preserve ended entries across sessions, including captured or lost outcomes after the goal later concludes. Reopen a lost or obsolete entry only when evidence explicitly establishes that the same opening is available and relevant again. Do not turn an ended entry into a different opportunity during wording cleanup. Captured, lost and obsolete are recorded outcomes, not invitations to invent historical openings.

### Final wording pass

Keep the title and all three detailed text fields brief and concrete. Check that the title conveys the opening, action and potential advantage in one sentence, or two short sentences when one would be crowded, without losing essential uncertainty. Retain enough context to understand and choose the action, including essential conditions, uncertainty and the identity of an ended opening, while removing discovery history and progress that no longer affect its use. Bring carried entries' detailed fields to the current structure. When a carried entry's facts, terms and lifecycle are unchanged, copy its existing title word for word; reword it only when it breaks the plain-wording rules in "Read-aloud wording for `title`" or when its facts, terms or lifecycle have changed. Do not invent a missing action, advantage or goal link to make a prior entry fit. Another category mentioning the same subject does not settle a distinct opening.

# Output Description

Return only a JSON object with the key `opportunities`, matching the supplied schema. Each entry has exactly the nine required properties defined above, including `title`, `id`, `parent_opportunity_id` and `lifecycle`. Retain all lifecycle values; an ended entry is not removed from this output. Use `null` for an absent impediment link and an empty array when nothing qualifies. Do not output another category, commentary or Markdown fences.

Example, only when the supplied goal and impediment establish these references and the Scene Log supports the claim:

{"opportunities":[{"id":"opportunity_new_1","title":"Father William says retrieving Sir Brandon's sword from the Barrow Mound could help slay the dragon.","opening":"Sir Brandon's sword lies at the Barrow Mound.","action":"Retrieve the sword from the Barrow Mound.","advantage":"Father William says it can overcome the dragon's scales, helping slay the dragon; its power remains untested.","goal_id":"goal_1","goal_impediment_title":"The dragon's impenetrable scales","lifecycle":"available","parent_opportunity_id":null}]}
