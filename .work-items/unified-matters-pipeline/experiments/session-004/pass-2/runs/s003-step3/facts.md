
## thread_1 Treasure map [earlier/open] parent=None
   Not touched this Session; the map's treasure is still unfound.
 - fact_1 want [medium/medium] Find the treasure marked on the party's map.
     carried | prior

## thread_2 Dragon hunt (Eric the Reeve's bounty) [earlier/open] parent=None
   Sir Phidipaldi obtained Sir Brandon's magic sword (beat_61), a major advance, but the dragon still lives and the rest of the plan in beat_3 remains to be carried out.
 - fact_2 want [high/medium] Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty.
     carried | prior
 - fact_3 blocked_by [high/medium] George says nothing pierces the black dragon's scales; arrows and swords have all failed against them.
     carried | prior
 - fact_4 threat [high/medium] George says the black dragon will soon fly and doom Brandonsford.
     carried | prior
 - fact_5 could_use [medium/medium] Lady Hilda will join the party against the dragon if they pay her.
     carried | prior
 - fact_6 could_use [high/low] Father William says the dragon can only be killed with the magic sword buried with Sir Brandon in the Barrow Mound.
     ended; ENDED: used up: the party recovered the sword from the Barrow Mound; replaced by fact_new_1 | prior, beat_59, beat_61
 - fact_7 could_use [medium/medium] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     carried | prior
 - fact_8 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_15 could_use [high/high] Sir Phidipaldi holds Sir Brandon's sword: magical, not cursed, silvery white, etched "All shadows yield to my light". Father William says only this sword can kill the dragon, and legend says it slew the old one.
     new; learned | prior, beat_4, beat_60, beat_61
 - fact_16 could_use [medium/medium] The tomb mosaics show Sir Brandon killed the old dragon by driving his sword up through the roof of its open mouth.
     new; learned | beat_10
 - fact_17 could_use [medium/high] Sir Phidipaldi's plan: use Sir Brandon's sword as proof of competence to press Eric the Reeve for an advance on the bounty, then use it to pay Lady Hilda and henchmen.
     new | beat_3
 - fact_18 could_use [medium/medium] The party plans to get protection against the black dragon's poison from the witch or the alchemist.
     new | beat_3

## thread_3 Missing shipments [earlier/open] parent=None
   Not touched this Session.
 - fact_9 unknown [medium/low] Why have shipments stopped reaching Brandonsford?
     carried | prior

## thread_4 Fairies appearing more often [earlier/open] parent=None
   Not touched this Session; the myth of a fairy-given sword does not bear on why fairies are appearing more often.
 - fact_10 unknown [medium/low] Why are hidden fairies coming out more often along with the dragon?
     carried | prior

## thread_5 Ingrid and Warwick (Dunk's deal) [earlier/open] parent=None
   Dunk's scheme to get Warwick's mithril shirt remains part of the party's plan (beat_3), and nothing owed under the deal has been done yet.
 - fact_11 owe [medium/medium] Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion.
     carried | prior
 - fact_19 want [high/medium] Obtain the mithril chain shirt that Warwick the smith displays, as protection for the dragon hunt.
     new; also thread_2 | beat_2, beat_3

## thread_6 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Dr. Uriah visited the Barrow Mound but did no penance or donation, so both obligations remain owed.
 - fact_12 owe [medium/high] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_13 owe [medium/medium] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior

## thread_7 Squints' share of the treasure [earlier/open] parent=None
   The party gathered its first treasure in the mound, but Squints has not yet been given his second pick, so the promise is still owed.
 - fact_14 owe [medium/high] The party must let Squints pick second from the first treasure, after the elite members.
     carried | prior, beat_21, beat_28, beat_48, beat_58

## thread_8 Drop Dead Ned's employment [new/open] parent=None
   The party hired Ned under an ongoing arrangement of kickbacks for murders and bodies, now extended to an offer for the dead goblins that is not yet carried out.
 - fact_20 could_use [medium/high] Drop Dead Ned, the inn's killer who carries a little killer wasp, is formally hired by the party for a 100 gold fee and is with them in the Barrow Mound as a scout.
     new | beat_1, beat_12, beat_40
 - fact_21 could_use [medium/medium] Ned pays the party 10 gold back each time they let him murder somebody, provided he can do whatever he wants with the body.
     new | beat_1
 - fact_22 could_use [medium/high] Ned offers a half-off rate of 5 gold per body for the three dead goblins in the Barrow Mound's lower corridor, which Wayman found fair; the party must hand the bodies over to collect.
     new; also thread_9 | beat_40, beat_41
 - fact_23 blocked_by [medium/medium] The Free Goblin Society would not want their dead compatriots defiled, so giving Ned the goblin bodies means sneaking them past the goblins.
     new; learned; about thread_9 | beat_42

## thread_9 The Free Goblin Society deal [new/open] parent=None
   The party promised to clear the evil from the mound and keep the goblins' presence from King Hogboon in exchange for Brandon's goods (beat_18); the mound is not yet cleared.
 - fact_24 owe [high/high] Under the bargain with the Free Goblin Society, the party must clear the evil out of the Barrow Mound so the goblins can live there.
     new; also thread_11 | beat_18
 - fact_25 owe [medium/low] Under the bargain with the Free Goblin Society, the party must not tell King Hogboon that the goblins are settled in the Barrow Mound.
     new; no definite end | beat_18
 - fact_26 could_use [medium/high] The Free Goblin Society agreed to walk with the party through the Barrow Mound and, rejecting property, lets the party take whatever it wants there.
     new | beat_18, beat_19
 - fact_27 unknown [low/medium] What is making the scratching sounds at the far west end of the Barrow Mound's lower corridor?
     new; learned | beat_43

## thread_10 Brother Dirk and the church's claim on the tomb's relics [new/open] parent=None
   Dr. Uriah wore Saint Arthur's holy robes over Dirk's objection and Trout deferred Dirk's claim that the chalice belongs to the church, leaving the dispute unsettled.
 - fact_28 unknown [medium/medium] Does the jeweled chalice (worth 600 gold) that Trout took from Sir Brandon's tomb belong to the church, as Brother Dirk suggests? Trout put off the question, saying they would figure it out later.
     new; also thread_7 | beat_56
 - fact_29 unknown [low/medium] Are the robes of Saint Arthur magical? Brother Dirk says they are far too holy to wear and objects to Dr. Uriah wearing them. Dr. Uriah could not test them without Ingrid's witch powder, and wearing them had no notable effect.
     new; learned | beat_30, beat_32, beat_33

## thread_11 The undead giant in the Barrow Mound [new/open] parent=None
   A huge undead swordsman matching Alfred from the mosaics has been killing goblins and has just appeared in the tomb doorway, an active danger.
 - fact_30 threat [high/high] A seven-foot undead brown skeleton in rusted armor and a mustachioed death mask, dragging a huge greatsword, stands in the doorway of Sir Brandon's tomb as the party tries to leave. The goblins and the pool slime say this big, very mad undead swordsman roams the Barrow Mound and has cut down many goblins.
     new; learned; also thread_9 | beat_26, beat_40, beat_46, beat_62
 - fact_31 unknown [medium/medium] Is the undead giant Alfred, the shaggy giant with a greatsword shown as Sir Brandon's companion in the mosaics, and what made him undead?
     new; learned | beat_10, beat_26, beat_62

standalone: [{'beat': 'beat_6', 'reason': "The recently disturbed door was a notable clue, explained by the goblins' arrival."}, {'beat': 'beat_11', 'reason': 'The real gemstones in the mosaics are a notable source of wealth left in the mound.'}, {'beat': 'beat_34', 'reason': "The four virtue statues supplied the answers that later opened Brandon's tomb."}, {'beat': 'beat_38', 'reason': "Sir Phidipaldi's blessing of good fortune lasts for the rest of the Barrow Mound adventure."}]
