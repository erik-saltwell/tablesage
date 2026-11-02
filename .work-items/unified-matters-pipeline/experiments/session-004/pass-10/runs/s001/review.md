# Session 001: what was kept and dropped

Pass 10. Every tracked fact and every "Last session..." candidate, with the field that decided it. Assets are state, not open matters. Mark any you disagree with.

## Last session... candidates

Rule (provisional): standalone beats rated low importance are dropped by code before assessment; threads/standalone events retain medium-or-high impact AND lasting consequence; an otherwise unrepresented encounter may also qualify with medium-or-high historical value, regardless of enduring consequence; no scene or character quota.

- **SHOWN** · impact medium, lasting high, 1 beats · encounter value None · *The treasure map*: The party arrived in Brandonsford following a treasure map whose marked locations they did not recognize. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value low · *Brandonsford's gate*: The party talked their way past a night watchman into Brandonsford and got directions to the town's inns. → same main event represented by thread_1
- **SHOWN** · impact medium, lasting medium, 3 beats · encounter value None · *The Clurichen of the riverbanks*: A frog named Reginald warned that a trickster Clurichen comes from the riverbanks into town every night, and Sir Phidipaldi's claims about it proved wrong. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 1 beats · encounter value low · *The river*: Dr. Uriah spoke with Reginald the frog, who warned of the Clurichen. → same main event represented by thread_2
- **SHOWN** · impact high, lasting high, 8 beats · encounter value None · *The black dragon near Brandonsford*: The party learned a black dragon threatens Brandonsford, and Eric the Reeve offered 1000 gold to whoever kills it and brings back its body. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *Hiring Lady Hilda*: Lady Hilda offered to join the party for pay against the dragon, and Sir Phidipaldi said they would return for her services. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 4 beats · encounter value None · *Drop Dead Ned's offer*: Drop Dead Ned, a murderous thief with a killer wasp, offered himself for hire at 100 gold a week, and Dr. Uriah said he would think about it. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 3 beats · encounter value None · *The missing shipments to Brandonsford*: The party learned no shipments have reached Brandonsford in months, including Bentley's overdue restock. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact high, lasting high, 3 beats · encounter value medium · *The Clumsy Fox Tavern*: At the Clumsy Fox the party met Lady Hilda, Bentley, Eric the Reeve and Drop Dead Ned, learning of the dragon bounty before Sir Phidipaldi's quarrel with Eric got him sent away. → same main event represented by thread_3, thread_4, thread_5, thread_7
- **SHOWN** · impact medium, lasting medium, 3 beats · encounter value None · *Sir Phidipaldi's quarrel with Eric the Reeve*: Sir Phidipaldi insulted Eric the Reeve, slapped him and challenged him to a duel, which Eric declined, and Bentley banished Phidipaldi to the Golden Egg for the night. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 4 beats · encounter value medium · *Farmer Gill's farm*: Dunk spent the evening drinking with Farmer Gill, who offered him a mule and lodging and shared dragon lore and town gossip. → encounter value medium; independent of lasting consequence
- **hidden** · impact low, lasting low, 3 beats · encounter value None · *Shamus the mule*: Farmer Gill offered Dunk the mule Shamus for 100 gold, and Dunk, asking to trade work, slept on the offer in Gill's barn. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Warwick's mithril chain shirt*: The party learned that Warwick the smith displays a superb mithril chain shirt he refuses to sell. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 3 beats · encounter value None · *Quinn's vanishing ale*: Quinn, whose ale vanishes nightly, hired Sir Phidipaldi for 100 gold to stage a fake ale shipment to catch the culprit he believes is Bentley. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 2 beats · encounter value medium · *The Golden Egg Tavern*: At the Golden Egg, Quinn told Sir Phidipaldi of his vanishing ale and hired him for a fake-shipment scheme. → same main event represented by thread_10

### Standalone beats dropped by code

- **hidden** · importance low · beat_2: Brandonsford has no guards or proper law enforcement; a rotating group of able-bodied men keeps night watch, and an ancient small stone wall surrounds the town. → standalone beat rated low importance (model's reason: Brandonsford has no real law enforcement, only a night watch, which is useful background but tied to no thread.)
- **hidden** · importance low · beat_3: When a night watchman challenged them, Sir Phidipaldi claimed the sacred law of Zeus for hospitality and Wayman said they came from Ithaca; the watchman let them in before nightfall and pointed out the two inns. → standalone beat rated low importance (model's reason: The party gained entry to town; this was consequential but left nothing open.)
- **hidden** · importance low · beat_12: The halfling owner Bentley gave Wayman a free first Fox Tail Brew, which tasted fantastic, and offered rooms at 10 silver a night; one gold would cover the whole party for multiple nights. → standalone beat rated low importance (model's reason: The party learned the lodging terms at the Clumsy Fox.)
- **hidden** · importance low · beat_31: Farmer Gill thinks Ingrid, who sells potions, is hot for Warwick and that Warwick may put up the charms to keep her away; he doesn't know what Warwick thinks of her, but she is where to go for potions. → standalone beat rated low importance (model's reason: Ingrid is where to get potions; this is a local resource not tied to any thread.)

## Hidden open facts

### Would have been under "Your goals"

- Get Farmer Gill's mule Shamus, which Gill offers to sell for 100 gold. *(Shamus the mule; fact_20)* → **significance incidental**
- Get Warwick the smith's mithril chain shirt. *(Warwick's mithril chain shirt; fact_22)* → **significance incidental**

### Would have been under "Standing in your way"

- Bentley forbids fighting at the Clumsy Fox and has ruled that Sir Phidipaldi must spend the night at the Golden Egg. *(Sir Phidipaldi's quarrel with Eric the Reeve; fact_19)* → **scene-local obstruction; not a lasting impediment**
- Farmer Gill says Warwick the smith displays his mithril chain shirt but always refuses to sell it. *(Warwick's mithril chain shirt; fact_23)* → **blocks no shown live want, debt or opening**

### Would have been under "What could help"

- Lady Hilda's offer to join the party for pay could add a seasoned fighter to the dragon hunt. *(The black dragon near Brandonsford; fact_11)* → **equivalent offer/plan shown as fact_12: Both facts describe the same offer from beat_10: Lady Hilda will join the party against the dragon for pay. Each has the same trigger (hiring her) and the same benefit (a seasoned armored fighter for the dragon hunt). Both help thread_3 as established openings.**
- Drop Dead Ned offers himself and his killer wasp for hire at 100 gold for the week, on condition that he gets to kill people with the wasp; he would give back 5 gold per killing he is allowed if he can do what he wants with the victims. Dr. Uriah said he would think about it. *(Drop Dead Ned's offer; fact_14)* → **not an extra enabling opening: generic_benefit (Trigger: paying Ned 100 gold to hire him and his wasp. Benefit: an extra killer, but no specific advantage toward any established want or debt was established.)**
- Asked whether Dunk could trade work for Shamus, Farmer Gill says the big work needed is killing the dragon outside town; no trade was agreed, and Gill's three sons are already trying to kill it. *(Shamus the mule; fact_21)* → **not an extra enabling opening: goal_pursuit (Trigger: kill the dragon as work for Gill; benefit: obtaining Shamus in place of the 100-gold price. This is paying the want's own price in another form.)**

### Would have been under "Still unanswered"

- Where is the treasure? *(The treasure map; fact_3)* → **investigative_depth low; narrative_payoff low**
- Where is the black dragon near Brandonsford? *(The black dragon near Brandonsford; fact_7)* → **investigative_depth low; narrative_payoff low**
- Where did this new dragon come from, given Sir Brandon's dragon was killed centuries ago? *(The black dragon near Brandonsford; fact_8)* → **grounding low; investigative_potential low**
- What is Drop Dead Ned's killer wasp? *(Drop Dead Ned's offer; fact_15)* → **grounding low; investigative_depth low; narrative_payoff low; investigative_potential low**

### Would have been under "Promises and debts"

- Sir Phidipaldi told Lady Hilda the party would talk with the Reeve and come back to hire her. *(Hiring Lady Hilda; fact_13)* → **commitment_type general_agreement**

### Would have been under "Meanwhile"

- Reginald the Frog warns that the Clurichen, a trickster up to no good, comes into town every night and that the party should stay away from wherever it goes. *(The Clurichen of the riverbanks; fact_5)* → **negative_outcome_clarity low; outcome_severity low**

## Stored assets (not open matters)

- The party holds a treasure map marking several locations they do not recognize. *(fact_2)*

## Shown open facts

### Your goals

- Find the treasure. *(The treasure map; fact_1)* → end; adventure
- Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000-gold bounty. *(The black dragon near Brandonsford; fact_6)* → end; adventure
- Help Quinn get back at Bentley, whom Quinn blames for stealing his ale at night, and collect Quinn's 100 gold. *(Quinn's vanishing ale; fact_24)* → end; side
- Sir Phidipaldi wants to fight Eric the Reeve in the duel at dawn he challenged him to. *(Sir Phidipaldi's quarrel with Eric the Reeve; fact_17)* → end; side

### Standing in your way

- Eric the Reeve has not accepted Sir Phidipaldi's duel challenge, only flusteredly saying Sir Phidipaldi is more skilled at adventure. *(Sir Phidipaldi's quarrel with Eric the Reeve; fact_18)* → active beyond scene; blocks thread_7

### What could help

- Quinn and Sir Phidipaldi plan a fake shipment: Quinn brings bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to see who comes for it. *(Quinn's vanishing ale; fact_25)* → opening; helps thread_10; support medium
- Eric says the woodsman George, who met the dragon and lives a couple of houses down from the Clumsy Fox, may come to the tavern tonight; the party could ask him what he saw and where. *(The black dragon near Brandonsford; fact_10)* → opening; helps thread_3; support medium
- If the party pays Lady Hilda, a seasoned fighter with chain mail and a shield, she will join them against the dragon. Her fee is unset, and she says she cannot kill the dragon herself; Sir Phidipaldi told her they would come back to hire her. *(Hiring Lady Hilda; fact_12)* → opening; helps thread_3; support medium

### Still unanswered

- Who or what empties and knocks over Quinn's stock each night? *(Quinn's vanishing ale; fact_26)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- What is the Clurichen up to when it comes from the riverbanks into Brandonsford every night? *(The Clurichen of the riverbanks; fact_4)* → open_ended; grounding medium, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- Why has nothing reached Brandonsford in months, including Bentley's tavern restock shipment that was due a week ago? *(The missing shipments to Brandonsford; fact_16)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium

### Meanwhile

- The black dragon outside Brandonsford, which tore off the woodsman George's arm, may maim or kill those who confront it, including Farmer Gill's three sons, who are hunting it now. *(The black dragon near Brandonsford; fact_9)* → external; negative_outcome_clarity high, outcome_severity high, evidentiary_strength medium, evidence_of_progression medium, preventability medium
