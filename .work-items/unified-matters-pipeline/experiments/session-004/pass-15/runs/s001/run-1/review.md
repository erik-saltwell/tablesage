# Session 001: what was kept and dropped

Pass 15. Every tracked fact and every "Last session..." candidate, with the field that decided it. Assets are state, not open matters. Mark any you disagree with.

## Last session... candidates

Rule (provisional): standalone beats rated low importance are dropped by code before assessment; threads/standalone events retain medium-or-high impact AND lasting consequence; an otherwise unrepresented encounter may also qualify with medium-or-high historical value, regardless of enduring consequence; no scene or character quota; validated main-event anchors sorted by Ledger position.

- **SHOWN** · impact medium, lasting high, 1 beats · encounter value None · *The unrecognized treasure map*: The party arrived in Brandonsford following a treasure map whose marked locations they could not recognize. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value low · *Brandonsford's gate*: The party talked their way past a night watchman into Brandonsford. → same main event represented by thread_1
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *Clurichen on the riverbanks*: Reginald the frog warned Dr. Uriah that a trickster Clurichen comes from the riverbanks into town every night. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 2 beats · encounter value low · *The river*: Dr. Uriah spoke with Reginald the frog, who warned of the Clurichen. → same main event represented by thread_3
- **hidden** · impact low, lasting medium, 1 beats · encounter value None · *Bentley's missing shipment*: The party learned Bentley's restocking shipment was a week overdue and nothing has reached town in months. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 2 beats · encounter value None · *Shamus the mule*: Farmer Gill offered Dunk his shabby mule Shamus for 100 gold or dragon-killing work, and Dunk slept in the barn to think it over. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 4 beats · encounter value medium · *Farmer Gill's farm*: Dunk spent the night drinking with Farmer Gill, hearing the legend of Sir Brandon and that Gill's sons were hunting the dragon. → encounter value medium; independent of lasting consequence
- **SHOWN** · impact high, lasting high, 3 beats · encounter value None · *The Brandonsford dragon and the Reeve's bounty*: Eric the Reeve offered 1000 gold to kill a black dragon that had torn off a woodsman's arm, but Sir Phidipaldi insulted him and challenged him to a duel. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact high, lasting high, 2 beats · encounter value low · *The Clumsy Fox Tavern*: At the Clumsy Fox, Sir Phidipaldi took up the dragon bounty talk with Eric the Reeve but ended up slapping him and being thrown out. → same main event represented by thread_2
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value None · *Drop Dead Ned's offer of hire*: Drop Dead Ned, a murderous thief with a killer wasp, offered to hire on with Dr. Uriah for 100 gold a week, and Uriah said he would think about it. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Standalone event*: Gill revealed that Warwick the smith is growing paranoid and keeps an unsellable mithril chain shirt on display. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting low, 1 beats · encounter value None · *Standalone event*: Bentley stopped Sir Phidipaldi's quarrel with Eric and banished him to the Golden Egg for the night while his friends stayed. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting high, 2 beats · encounter value None · *Quinn's vanishing ale*: Sir Phidipaldi agreed to help Quinn for 100 gold by staging a fake ale delivery to catch whoever empties his stock each night. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting high, 1 beats · encounter value low · *The Golden Egg Tavern*: At the Golden Egg, Sir Phidipaldi agreed to stage a fake ale delivery for Quinn. → same main event represented by thread_7

### Standalone beats dropped by code

- **hidden** · importance low · beat_2: Brandonsford has no guards or proper law enforcement; a rotating group of able-bodied men keeps the night watch. → standalone beat rated low importance (model's reason: Background on Brandonsford's lack of law enforcement, not tied to any thread.)
- **hidden** · importance low · beat_4: Brandonsford has a general store, a smith, a small church, an alchemist shop and a farm on the edge of town; the Clumsy Fox Tavern is busy and warm, while the Golden Egg Tavern across the street has fewer people. → standalone beat rated low importance (model's reason: Layout of the town's shops and inns, general background.)
- **hidden** · importance low · beat_28: Gill says Warwick has covered a wall of his shop with clovers, and guesses the charms may be to keep away Ingrid, the potion seller, who is hot for Warwick; Ingrid is where to go for potions. → standalone beat rated low importance (model's reason: Gossip about Ingrid the potion seller and Warwick's clovers, pointing to where potions can be bought.)

## Hidden open facts

### Would have been under "Your goals"

- Get Farmer Gill's mule Shamus. *(Shamus the mule; fact_15)* → **significance incidental**

### Would have been under "What could help"

- Farmer Gill offers Dunk his mule Shamus for 100 gold, or in trade for work, the big work being killing the dragon outside town. *(Shamus the mule; fact_16)* → **not an extra enabling opening: goal_pursuit (The trigger is paying 100 gold or killing the dragon; the benefit is simply obtaining the mule, which is the want itself, so the action pays the item's own price.)**

### Would have been under "Still unanswered"

- What is the Clurichen doing in town each night? *(Clurichen on the riverbanks; fact_11)* → **narrative_payoff low**

### Would have been under "Meanwhile"

- Reginald the frog says a little trickster creature called a Clurichen comes from the riverbanks into town every night, up to no good, and that the party should stay away from wherever it goes. *(Clurichen on the riverbanks; fact_10)* → **negative_outcome_clarity low; outcome_severity low**
- With no shipments reaching Brandonsford, the town's supplies are running short; Bentley says the missing shipment is hurting the whole town, and Gill says Warwick the smith has little left to sell. *(Bentley's missing shipment; fact_13)* → **outcome_severity low**

## Stored assets (not open matters)

- The party holds a treasure map with several marked locations, one of which they assume holds the treasure. *(fact_3)*
- George, a woodsman living a couple of houses from the Clumsy Fox, encountered the dragon and describes it as a black dragon, not a big one. *(fact_6)*

## Shown open facts

### Your goals

- Find the treasure shown on the party's map. *(The unrecognized treasure map; fact_1)* → end; adventure
- Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000 gold. *(The Brandonsford dragon and the Reeve's bounty; fact_4)* → end; adventure
- Catch whoever empties Quinn's good ale stock at the Golden Egg each night and collect Quinn's 100 gold. *(Quinn's vanishing ale; fact_17)* → end; side

### What could help

- Lady Hilda, a seasoned fighter in chain mail with a shield, offers to join the party for pay to hunt the dragon; she won't go alone. *(The Brandonsford dragon and the Reeve's bounty; fact_5)* → opening; helps thread_2; support medium
- Drop Dead Ned offers himself and his killer wasp for hire at 100 gold a week, doing anything as long as he gets to kill people with the wasp; Dr. Uriah said he would think about it. *(Drop Dead Ned's offer of hire; fact_14)* → opening; helps thread_2; support low
- Quinn and Sir Phidipaldi have planned a fake ale delivery: Quinn brings bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to the Golden Egg to see who comes for it. *(Quinn's vanishing ale; fact_18)* → opening; helps thread_7; support medium

### Still unanswered

- Where are the locations marked on the party's treasure map, and at which one does the treasure lie? *(The unrecognized treasure map; fact_2)* → adventure objective for thread_1; grounded and investigable; independent depth/payoff not required
- Who or what empties Quinn's good ale each night, leaving half the glasses empty or knocked over? Quinn believes it is Bentley. *(Quinn's vanishing ale; fact_19)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- Where does the black dragon lurk outside Brandonsford? *(The Brandonsford dragon and the Reeve's bounty; fact_8)* → adventure objective for thread_2; grounded and investigable; independent depth/payoff not required
- What happened to Bentley's restocking shipment, a week overdue, and why has nothing come into Brandonsford in months? *(Bentley's missing shipment; fact_12)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- Where did this new dragon come from, when Sir Brandon's dragon was killed centuries ago and none has appeared since? *(The Brandonsford dragon and the Reeve's bounty; fact_7)* → open_ended; grounding medium, investigative_depth medium, narrative_payoff medium, investigative_potential medium

### Meanwhile

- The black dragon near Brandonsford tore off the woodsman George's arm and may maim or kill others, including Gill's three sons, who are hunting it now. *(The Brandonsford dragon and the Reeve's bounty; fact_9)* → external; negative_outcome_clarity medium, outcome_severity high, evidentiary_strength medium, evidence_of_progression medium, preventability medium
