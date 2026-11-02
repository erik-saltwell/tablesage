# Session 001: what was kept and dropped

Pass 12. Every tracked fact and every "Last session..." candidate, with the field that decided it. Assets are state, not open matters. Mark any you disagree with.

## Last session... candidates

Rule (provisional): standalone beats rated low importance are dropped by code before assessment; threads/standalone events retain medium-or-high impact AND lasting consequence; an otherwise unrepresented encounter may also qualify with medium-or-high historical value, regardless of enduring consequence; no scene or character quota; validated main-event anchors sorted by Ledger position.

- **SHOWN** · impact high, lasting high, 1 beats · encounter value None · *The treasure map*: The party arrived at Brandonsford following a treasure map whose marked locations they don't recognize. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 0 beats · encounter value low · *Brandonsford's town wall*: A night watchman let the party into Brandonsford after Sir Phidipaldi invoked Zeus's law of hospitality. → same main event represented by thread_1
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *The Clurichen*: Reginald the Frog warned that a trickster Clurichen comes from the riverbanks into town every night. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 1 beats · encounter value low · *The riverbank*: Dr. Uriah spoke with Reginald the Frog, who warned of a nightly Clurichen. → same main event represented by thread_3
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *Lady Hilda's offer to join the hunt*: Lady Hilda offered to join the dragon hunt for pay, and Sir Phidipaldi said they would return to hire her. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value None · *Brandonsford's missing shipments*: The party learned that shipments into Brandonsford have stopped, leaving Bentley's restock a week overdue and the smith with little to sell. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Shamus the mule*: Farmer Gill offered Dunk the shabby mule Shamus for 100 gold, and Dunk is thinking it over. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value medium · *Farmer Gill's farm*: Dunk spent the evening drinking with Farmer Gill, who offered his mule, told the tale of Sir Brandon's dragon slaying, and shared town gossip. → encounter value medium; independent of lasting consequence
- **SHOWN** · impact high, lasting high, 3 beats · encounter value None · *The Brandonsford dragon*: Eric the Reeve offered 1000 gold to whoever kills the black dragon troubling Brandonsford and drags its body into town. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact high, lasting high, 3 beats · encounter value low · *The Clumsy Fox Tavern*: At the Clumsy Fox, the party met Lady Hilda, Bentley, Eric the Reeve and Drop Dead Ned, took up the dragon bounty, and Sir Phidipaldi's quarrel with the Reeve got him sent away. → same main event represented by thread_2, thread_4, thread_6
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Standalone event*: Sir Phidipaldi slapped Eric the Reeve with his glove and challenged him to a duel at dawn, which Eric did not accept. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *Drop Dead Ned's offer*: Drop Dead Ned offered himself and his killer wasp for hire at 100 gold a week, and Dr. Uriah said he'd think about it. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Standalone event*: Bentley sent Sir Phidipaldi to spend the night at the Golden Egg after his argument with the Reeve grew heated. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value None · *Quinn's fake shipment scheme*: Sir Phidipaldi agreed to Quinn's 100-gold plan to stage a fake ale delivery and catch whoever empties his bar at night. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 1 beats · encounter value low · *The Golden Egg Tavern*: Quinn hired Sir Phidipaldi to stage a fake ale shipment to catch the nightly thief of his bar. → same main event represented by thread_8

### Standalone beats dropped by code

- **hidden** · importance low · beat_3: Brandonsford has no guards or proper law enforcement; a rotating group of able-bodied men keeps night watch. → standalone beat rated low importance (model's reason: Background on the town's lack of law enforcement.)
- **hidden** · importance low · beat_4: Brandonsford has a general store, a smith, a small church, an alchemist shop and a farm on the edge of town; the Clumsy Fox is busy and cozy, the Golden Egg nearly empty. → standalone beat rated low importance (model's reason: Background on the town's shops and inns.)
- **hidden** · importance low · beat_6: Dr. Uriah used his once-daily power to speak with aquatic animals at the river to ask which tavern was better, and found a frog named Reginald, who didn't know. → standalone beat rated low importance (model's reason: Dr. Uriah spent his daily power speaking with Reginald.)
- **hidden** · importance low · beat_12: Wayman met the halfling owner Bentley, who gave him a free, fantastic-tasting Fox Tail Brew and offered rooms at 10 silver a night. → standalone beat rated low importance (model's reason: Bentley offered rooms at 10 silver a night.)
- **hidden** · importance low · beat_30: Farmer Gill says Warwick is increasingly paranoid, adding lucky charms to his shop daily and covering a wall with clovers; Gill guesses it is to keep away Ingrid the potion seller, who is hot for Warwick. → standalone beat rated low importance (model's reason: Warwick's growing paranoia and lucky charms, with no thread attached yet.)
- **hidden** · importance low · beat_33: At the empty Golden Egg, owner Quinn charged Sir Phidipaldi 10 silver for terrible watered-down ale, three times the Clumsy Fox's price. → standalone beat rated low importance (model's reason: Quinn overcharged Sir Phidipaldi for watered ale.)

## Hidden open facts

### Would have been under "Your goals"

- Dunk wants Farmer Gill's mule Shamus, which Gill will sell for 100 gold. *(Shamus the mule; fact_16)* → **significance incidental**

### Would have been under "What could help"

- Lady Hilda's offer to join the hunt for pay (thread_4) could add a seasoned fighter against the dragon. *(The Brandonsford dragon; fact_9)* → **equivalent offer/plan shown as fact_12: Both facts describe the same offer from beat_10. Lady Hilda, a seasoned, armored fighter, will join the dragon hunt if the party pays her. Both serve thread_2 with the same form and certainty. fact_12 is the home representation in thread_4.**
- Farmer Gill would accept work in place of the 100 gold for Shamus, and says the big work he needs is killing the dragon. *(Shamus the mule; fact_17)* → **not an extra enabling opening: goal_pursuit (Trigger: killing the dragon as work for Gill; benefit: Gill gives Dunk the mule without the 100 gold. This is simply meeting Gill's alternative terms for the very mule wanted.)**

### Would have been under "Still unanswered"

- What will become of Farmer Gill's three sons, who are out trying to kill the dragon now? *(The Brandonsford dragon; fact_8)* → **ordinary information gap, not an investigative objective**
- What does the Clurichen do when it comes into town each night? *(The Clurichen; fact_11)* → **narrative_payoff low**

### Would have been under "Promises and debts"

- Sir Phidipaldi told Lady Hilda the party would talk to the Reeve and come back to hire her. *(Lady Hilda's offer to join the hunt; fact_13)* → **commitment_type general_agreement**

### Would have been under "Meanwhile"

- Reginald the Frog warns that a little trickster creature called a Clurichen comes from the riverbanks into Brandonsford every night, up to no good, and that the party should stay away from wherever it goes. *(The Clurichen; fact_10)* → **negative_outcome_clarity low; outcome_severity low**

## Stored assets (not open matters)

- The party holds a treasure map marking several locations around Brandonsford that they don't recognize; they assume the treasure is at one of them. *(fact_2)*

## Shown open facts

### Your goals

- Find the treasure marked on the party's treasure map. *(The treasure map; fact_1)* → end; adventure
- Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000 gold. *(The Brandonsford dragon; fact_4)* → end; adventure
- Catch whoever empties the Golden Egg's bar at night, which Quinn blames on Bentley, and collect Quinn's 100 gold. *(Quinn's fake shipment scheme; fact_18)* → end; side

### What could help

- Sir Phidipaldi and Quinn agreed a plan: Quinn brings bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to the Golden Egg to lure whoever empties the bar. *(Quinn's fake shipment scheme; fact_19)* → opening; helps thread_8; support medium
- Eric the Reeve says the woodsman George, who met the dragon and lost an arm to it, lives a couple of houses down and may come to the Clumsy Fox tonight; the party could question him about where and how he encountered it. *(The Brandonsford dragon; fact_5)* → opening; helps thread_2; support medium
- Lady Hilda, a seasoned fighter in chain mail and shield, would join the party's dragon hunt for pay. Her fee is not yet set. *(Lady Hilda's offer to join the hunt; fact_12)* → opening; helps thread_2; support medium
- Drop Dead Ned, a murderous thief with a killer wasp in a jar, offers to hire on with the party for 100 gold a week, willing to do anything as long as he gets to kill people; Dr. Uriah said he'd think about it. *(Drop Dead Ned's offer; fact_15)* → opening; helps thread_2; support low

### Still unanswered

- Who or what empties and knocks over the Golden Egg's stock every night? Quinn blames Bentley. *(Quinn's fake shipment scheme; fact_20)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- Where are the locations marked on the treasure map, and which one holds the treasure? *(The treasure map; fact_3)* → adventure objective for thread_1; grounded and investigable; independent depth/payoff not required
- Where can the black dragon be found? *(The Brandonsford dragon; fact_6)* → adventure objective for thread_2; grounded and investigable; independent depth/payoff not required
- Why have shipments stopped reaching Brandonsford? Bentley's tavern restock is a week overdue, and Farmer Gill says nothing has come into town in months. *(Brandonsford's missing shipments; fact_14)* → open_ended; grounding medium, investigative_depth medium, narrative_payoff medium, investigative_potential medium

### Meanwhile

- The black dragon, which took woodsman George's arm, remains loose around Brandonsford and may maim those who confront it. *(The Brandonsford dragon; fact_7)* → external; negative_outcome_clarity high, outcome_severity medium, evidentiary_strength high, evidence_of_progression medium, preventability medium
