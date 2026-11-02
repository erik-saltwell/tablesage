
## thread_1 The unrecognized treasure map [new/open] parent=None
   The party is following a treasure map whose marked locations they don't recognize, and the treasure's whereabouts remain unknown.
 - fact_1 want [high/medium] Find the treasure shown on the party's treasure map, which the party assumes lies at one of the map's marked spots.
     new | beat_1
 - fact_2 unknown [high/medium] Where are the locations marked on the party's treasure map? The party doesn't recognize them, and the land around Brandonsford is wholly unknown to them.
     new | beat_1

## thread_2 The Clurichen of the riverbanks [new/open] parent=None
   Reginald warned of a trickster creature that comes into town nightly and should be avoided; this danger stands on its own and is still open.
 - fact_3 threat [medium/medium] Reginald the Frog warns that every night a little trickster creature called a Clurichen comes from the riverbanks into Brandonsford, up to no good, and that the party should stay away from wherever it goes.
     new; learned | beat_7

## thread_3 The dragon near Brandonsford [new/open] parent=None
   A black dragon troubles the town and Eric the Reeve offers 1000 gold for its body; leads (George, Gill's sighting, the Sir Brandon legend) and rivals (Gill's sons) all bear on this one hunt, which is not yet done.
 - fact_4 want [high/medium] Kill the black dragon near Brandonsford.
     new; UNCERTAIN: The party never formally took the job. Sir Phidipaldi said they would talk to the Reeve and return for Lady Hilda, but he also told Eric that black dragons don't exist. | beat_10, beat_16
 - fact_5 could_use [high/medium] Eric the Reeve offers 1000 gold to whoever kills the dragon and drags its body into Brandonsford.
     new; learned; also thread_6 | beat_16
 - fact_6 could_use [high/high] The one-armed woodsman George encountered the dragon and describes it as a black dragon, not a big one. Eric says he lives a couple of houses down from the Clumsy Fox and might come to the tavern tonight.
     new; learned | beat_17
 - fact_7 could_use [medium/high] Lady Hilda's offer to join the dragon hunt for pay could help the party fight the dragon.
     new; about thread_4 | beat_10
 - fact_8 threat [medium/medium] A black dragon lurks near Brandonsford. It tore off the woodsman George's arm and may harm others.
     new; learned | beat_13, beat_17, beat_29
 - fact_9 threat [high/medium] Farmer Gill's three sons are out hunting the dragon now, and Gill is sure they will bring it back. They may kill it and claim the Reeve's bounty before the party does.
     new; learned | beat_30
 - fact_10 unknown [high/medium] Where is the dragon to be found outside Brandonsford?
     new | beat_17, beat_27, beat_29
 - fact_11 unknown [low/low] Sir Brandon's dragon was killed and ripped apart centuries ago. Where did this new dragon come from?
     new; learned | beat_28, beat_29

## thread_4 Hiring Lady Hilda [new/open] parent=thread_3
   Lady Hilda offered to join for money against the dragon, and Sir Phidipaldi said they would come back for her after talking to the Reeve (beat_10), so it serves the dragon hunt and is still pending.
 - fact_12 could_use [medium/high] Lady Hilda, a seasoned red-headed noblewoman in chain mail and shield at the Clumsy Fox, will join the party against the dragon for pay (fee not yet named), though she says she couldn't kill it herself. Sir Phidipaldi told her they would come back for her services after talking to the Reeve.
     new; also thread_3 | beat_10

## thread_5 Bentley's missing shipment [new/open] parent=None
   Bentley's restock shipment is a week overdue and nothing has reached town in months; no one is known to have gone after it.
 - fact_13 unknown [medium/medium] What has stopped shipments from reaching Brandonsford for months, and what happened to Bentley's tavern restock shipment that was due a week ago?
     new; learned; also thread_9,thread_10 | beat_14, beat_33, beat_40

## thread_6 Sir Phidipaldi's challenge to Eric the Reeve [new/open] parent=None
   Sir Phidipaldi slapped Eric and challenged him to a dawn duel, which Eric never accepted (beat_19); Bentley banned fighting and ejected Phidipaldi (beat_24), but the quarrel is unsettled.
 - fact_14 want [medium/medium] Sir Phidipaldi intends to fight Eric the Reeve in the duel at dawn he demanded after slapping him with his glove.
     new | beat_19
 - fact_15 blocked_by [medium/medium] Eric the Reeve has not accepted Sir Phidipaldi's challenge; he only said, flustered, that Sir Phidipaldi was more skilled at adventure. This blocks the dawn duel.
     new | beat_19
 - fact_16 blocked_by [low/low] Bentley, owner of the Clumsy Fox, has banned fighting between Sir Phidipaldi and Eric the Reeve and sent Sir Phidipaldi to sleep at the Golden Egg, which constrains pursuing the duel at his tavern.
     new | beat_24

## thread_7 Drop Dead Ned's offer of hire [new/open] parent=None
   Ned offered himself and his killer wasp for 100 gold a week, and Dr. Uriah said he'd think about it, so the offer stands.
 - fact_17 could_use [medium/high] Drop Dead Ned, a greasy-haired thief at the Clumsy Fox, offers himself and his killer wasp for hire at 100 gold a week, willing to do anything as long as he gets to kill people with the wasp. He offers a 5-gold rebate per kill if he can do what he wants with the victims. Dr. Uriah said he'd think about it; accepting requires paying the fee.
     new; learned | beat_20, beat_21, beat_22, beat_23

## thread_8 Shamus the mule [new/open] parent=None
   Gill offered to sell Shamus for 100 gold, Dunk asked to trade work instead, and Dunk is still thinking it over.
 - fact_18 could_use [medium/high] Farmer Gill offers to sell Dunk his shabby mule Shamus for 100 gold.
     new | beat_26, beat_32
 - fact_19 could_use [medium/medium] Dunk asked to trade work for Shamus instead of paying; Farmer Gill says the big work needed is killing the dragon outside town. Gill never said that killing it would pay for the mule.
     new; learned; UNCERTAIN: Gill named the work needed but never confirmed that killing the dragon would pay for Shamus.; about thread_3; also thread_3 | beat_26, beat_27, beat_32

## thread_9 Warwick the smith and his mithril shirt [new/open] parent=None
   Warwick displays a superb mithril chain shirt he refuses to sell and is growing strangely paranoid, both open matters the party might act on.
 - fact_20 unknown [medium/medium] Gill says Warwick the smith displays a superb mithril chain shirt, perhaps the best in the world and sized for a normal-sized person, but always refuses to sell it. Why won't Warwick sell the mithril shirt?
     new; learned | beat_33
 - fact_21 unknown [medium/medium] Gill says Warwick is growing more paranoid, adding lucky charms to his shop daily and covering a wall with clovers; Gill guesses they are meant to keep away Ingrid the potion seller, who he says is hot for Warwick. What is Warwick really warding against?
     new; learned | beat_33, beat_34
 - fact_22 could_use [low/high] Gill says Ingrid, who runs the alchemist shop in Brandonsford, is where to go for potions; the party could visit her to buy them.
     new; learned | beat_34

## thread_10 Quinn's vanishing ale [new/open] parent=None
   Quinn's stock disappears nightly and he suspects Bentley; Sir Phidipaldi agreed to help for 100 gold and planned a fake shipment, which is still to be carried out.
 - fact_23 owe [high/high] Sir Phidipaldi agreed to help Quinn, owner of the Golden Egg, get back at Bentley, whom Quinn believes steals his ale each night, in exchange for 100 gold.
     new | beat_38, beat_39
 - fact_24 could_use [medium/medium] Quinn offers Sir Phidipaldi 100 gold for helping him get back at Bentley, payable once the help is given.
     new | beat_39
 - fact_25 could_use [high/high] Plan agreed with Quinn: stage a fake shipment at the Golden Egg. Quinn brings up bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to see what happens overnight.
     new | beat_40
 - fact_26 unknown [high/high] Quinn says his good stock is gone by morning, with half the glasses empty or knocked over, and blames Bentley because the Clumsy Fox is so popular. Who or what is really taking Quinn's ale each night?
     new; learned | beat_38

standalone: []
