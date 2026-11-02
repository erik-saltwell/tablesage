# Session 001: what was kept and dropped

Pass 11. Every tracked fact and every "Last session..." candidate, with the field that decided it. Assets are state, not open matters. Mark any you disagree with.

## Last session... candidates

Rule (provisional): standalone beats rated low importance are dropped by code before assessment; threads/standalone events retain medium-or-high impact AND lasting consequence; an otherwise unrepresented encounter may also qualify with medium-or-high historical value, regardless of enduring consequence; no scene or character quota.

- **SHOWN** · impact high, lasting high, 1 beats · encounter value None · *The unrecognized treasure map*: The party arrived in Brandonsford following a treasure map whose marked locations they did not recognize. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value low · *Brandonsford's town wall*: The night watchman let the party into Brandonsford after Sir Phidipaldi invoked Zeus's law of hospitality. → same main event represented by thread_1
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *The Clurichen from the riverbanks*: Reginald the frog warned Dr. Uriah that a trickster Clurichen comes from the riverbanks into town every night. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 1 beats · encounter value low · *The river*: Dr. Uriah spoke with Reginald the frog, who warned of the Clurichen. → same main event represented by thread_2
- **SHOWN** · impact high, lasting high, 7 beats · encounter value None · *The dragon and the Reeve's bounty*: Eric the Reeve offered 1000 gold for the body of a black dragon troubling Brandonsford, and the party gathered accounts of it. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 1 beats · encounter value None · *Lady Hilda's offer to join the dragon hunt*: Lady Hilda offered to join the party's dragon hunt for pay, and Sir Phidipaldi promised to return for her services. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 3 beats · encounter value None · *Drop Dead Ned's offer of hire*: Drop Dead Ned offered himself and his killer wasp for hire at 100 gold a week, and Dr. Uriah said he would think about it. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value None · *Brandonsford's missing shipments*: The party learned that shipments to Brandonsford have stopped arriving for months, leaving the town short of goods. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact high, lasting high, 3 beats · encounter value high · *The Clumsy Fox Tavern*: At the Clumsy Fox the party learned of the dragon bounty, met potential hirelings, and Sir Phidipaldi's quarrel with the Reeve got him sent away. → same main event represented by thread_3, thread_4, thread_5, thread_7
- **SHOWN** · impact medium, lasting medium, 4 beats · encounter value None · *Sir Phidipaldi's quarrel with Eric the Reeve*: Sir Phidipaldi insulted Eric the Reeve and challenged him to a duel, and Bentley sent him off to the Golden Egg for the night. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 4 beats · encounter value medium · *Farmer Gill's farm*: Dunk spent the evening with Farmer Gill, who offered his mule, shared Brandonsford's dragon history and town gossip, and hosted him in his barn. → encounter value medium; independent of lasting consequence
- **hidden** · impact low, lasting low, 2 beats · encounter value None · *Buying Shamus the mule*: Farmer Gill offered Dunk the mule Shamus for 100 gold or the dragon's death, and Dunk slept in Gill's barn to think it over. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact low, lasting low, 1 beats · encounter value None · *Standalone event*: Dunk learned that Warwick the smith displays a superb mithril chain shirt that he refuses to sell. → thread/event requires impact and lasting consequence both medium or high
- **SHOWN** · impact medium, lasting medium, 2 beats · encounter value None · *Quinn's vanishing ale and the fake shipment*: Sir Phidipaldi agreed to help Quinn stage a fake ale shipment to get back at Bentley, for 100 gold. → thread/event requires impact and lasting consequence both medium or high
- **hidden** · impact medium, lasting medium, 2 beats · encounter value medium · *The Golden Egg Tavern*: At the Golden Egg, Sir Phidipaldi heard Quinn's complaint of vanishing stock and agreed to stage a fake shipment against Bentley. → same main event represented by thread_9

### Standalone beats dropped by code

- **hidden** · importance low · beat_2: Brandonsford has no guards or proper law enforcement; a rotating group of able-bodied men keeps night watch. An ancient small stone wall surrounds the town. → standalone beat rated low importance (model's reason: The town has no real law enforcement, only a rotating night watch, which may matter later.)
- **hidden** · importance low · beat_28: Dunk told Gill he isn't sure what he is, having been sent out of his village when little. → standalone beat rated low importance (model's reason: Dunk revealed he was sent out of his village young and doesn't know what he is.)
- **hidden** · importance low · beat_32: Farmer Gill says Ingrid sells potions and is hot for Warwick, and guesses Warwick's charms might be meant to keep her away, though he doesn't know what Warwick thinks of her. → standalone beat rated low importance (model's reason: Gossip about Ingrid's interest in Warwick, with no pursuit.)

## Hidden open facts

### Would have been under "Your goals"

- Buy Shamus the mule from Farmer Gill, who asks 100 gold. *(Buying Shamus the mule; fact_17)* → **significance incidental**

### Would have been under "What could help"

- The woodsman George, who lives a couple of houses from the Clumsy Fox, encountered the black dragon and lost an arm to it; the party could ask him where he met it. *(The dragon and the Reeve's bounty; fact_8)* → **a step toward another opening**
- Lady Hilda, a seasoned fighter who says she can't hunt the dragon alone, offers to join the party for money to hunt it. *(Lady Hilda's offer to join the dragon hunt; fact_11)* → **equivalent offer/plan shown as fact_7: Both facts record the same offer from beat_10. Lady Hilda, a seasoned armoured fighter who cannot hunt the dragon alone, would join the party's dragon hunt for money. Both have the same trigger (hiring her for pay) and the same benefit (her combat help against the dragon), and both help thread_3. They share the established certainty and the opening form.**
- Farmer Gill would accept killing the dragon outside town as work in trade for Shamus instead of 100 gold. *(Buying Shamus the mule; fact_18)* → **not an extra enabling opening: goal_pursuit (Trigger: killing the dragon. Benefit: it pays Gill's price for Shamus in place of gold. This simply meets the want's own terms of sale.)**

### Would have been under "Still unanswered"

- Where does the treasure lie? *(The unrecognized treasure map; fact_3)* → **investigative_depth low; narrative_payoff low**
- What does the Clurichen do when it comes into town at night? *(The Clurichen from the riverbanks; fact_5)* → **grounding low; narrative_payoff low**
- Where is the black dragon, and where did it come from? *(The dragon and the Reeve's bounty; fact_9)* → **narrative_payoff low**

### Would have been under "Promises and debts"

- Sir Phidipaldi told Lady Hilda the party would talk with the Reeve and come back to take up her services. *(Lady Hilda's offer to join the dragon hunt; fact_12)* → **commitment_type general_agreement**

### Would have been under "Meanwhile"

- Reginald the frog says a little trickster creature called a Clurichen comes from the riverbanks into town every night, up to no good, and that the party should stay away wherever it goes. *(The Clurichen from the riverbanks; fact_4)* → **negative_outcome_clarity low; outcome_severity low**

## Stored assets (not open matters)

- The party holds a treasure map marking several locations they don't recognize; they assume the treasure is probably at one of them. *(fact_2)*

## Shown open facts

### Your goals

- Find the treasure the party is seeking. *(The unrecognized treasure map; fact_1)* → end; adventure
- Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000 gold bounty. *(The dragon and the Reeve's bounty; fact_6)* → end; adventure
- Help Quinn get back at Bentley, whom Quinn blames for stealing his ale at night, and collect Quinn's 100 gold. *(Quinn's vanishing ale and the fake shipment; fact_19)* → end; side
- Sir Phidipaldi wants to fight Eric the Reeve in a duel at dawn. *(Sir Phidipaldi's quarrel with Eric the Reeve; fact_15)* → end; side

### Standing in your way

- Eric the Reeve, offended by Sir Phidipaldi's false claims about George's dragon and the glove slap, did not accept the dawn duel, saying only that Sir Phidipaldi is more skilled at adventure. *(Sir Phidipaldi's quarrel with Eric the Reeve; fact_16)* → active beyond scene; blocks thread_7

### What could help

- If the party pays Lady Hilda, a seasoned fighter in chain mail and shield who says she can't hunt the dragon alone, she will join their dragon hunt, though her fee is not yet set. *(The dragon and the Reeve's bounty; fact_7)* → opening; helps thread_3; support medium
- Drop Dead Ned offers himself and his killer wasp for hire at 100 gold a week, doing anything as long as he gets to kill; he will refund 5 gold per kill he is allowed if he can do what he wants with the bodies. *(Drop Dead Ned's offer of hire; fact_13)* → opening; helps thread_3; support low
- Sir Phidipaldi and Quinn agreed to stage a fake ale shipment: Quinn brings bottles to fill with water and Sir Phidipaldi makes a big show of delivering them. *(Quinn's vanishing ale and the fake shipment; fact_20)* → opening; helps thread_9; support medium

### Still unanswered

- Why has nothing, including Bentley's restock shipment, come into Brandonsford for months? *(Brandonsford's missing shipments; fact_14)* → open_ended; grounding medium, investigative_depth medium, narrative_payoff medium, investigative_potential medium
- Who or what empties Quinn's good stock at the Golden Egg every night? *(Quinn's vanishing ale and the fake shipment; fact_21)* → open_ended; grounding high, investigative_depth medium, narrative_payoff medium, investigative_potential medium

### Meanwhile

- The black dragon outside Brandonsford, which tore off the woodsman George's arm, may maim others who encounter it. *(The dragon and the Reeve's bounty; fact_10)* → external; negative_outcome_clarity high, outcome_severity medium, evidentiary_strength medium, evidence_of_progression medium, preventability medium
