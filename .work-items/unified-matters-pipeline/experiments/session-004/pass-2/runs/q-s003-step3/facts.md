
## thread_1 Treasure map [earlier/open] parent=None
   Not touched this Session; the Barrow Mound treasure is not tied to the map.
 - fact_1 want [medium/low] Find the treasure marked on the party's map.
     carried | prior

## thread_2 Dragon hunt (Eric the Reeve's bounty) [earlier/open] parent=None
   Sir Phidipaldi took Sir Brandon's magic sword (beat_61) and the party set out a plan, but the dragon still lives, so the hunt continues with an added resource.
 - fact_2 want [high/medium] Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty.
     carried | prior
 - fact_3 blocked_by [high/medium] George says nothing pierces the black dragon's scales; arrows and swords have all failed against them.
     carried | prior
 - fact_4 threat [high/medium] George says the black dragon will soon fly and doom Brandonsford.
     carried | prior
 - fact_5 could_use [medium/medium] Lady Hilda will join the party against the dragon if they pay her.
     carried | prior
 - fact_6 could_use [high/high] Sir Phidipaldi holds Sir Brandon's magical, uncursed sword of silvery white metal etched "All shadows yield to my light"; Father William says only this sword can kill the dragon.
     updated; learned | prior, beat_59, beat_60, beat_61
 - fact_7 could_use [medium/medium] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     carried | prior
 - fact_8 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_15 could_use [medium/medium] Sir Phidipaldi's plan: show Sir Brandon's sword to Eric the Reeve as proof of competence to strong-arm him into an advance on the bounty, then use the advance to pay Lady Hilda and henchmen.
     new | beat_3
 - fact_16 could_use [medium/low] The Barrow Mound mosaics show Sir Brandon slaying the old dragon by driving his sword up through the roof of its open mouth.
     new; learned | beat_10, beat_4

## thread_3 Missing shipments [earlier/open] parent=None
   Not touched this Session.
 - fact_9 unknown [medium/low] Why have shipments stopped reaching Brandonsford?
     carried | prior

## thread_4 Fairies appearing more often [earlier/open] parent=None
   Not touched this Session; the myth of a fairy-given sword does not explain why fairies are appearing.
 - fact_10 unknown [medium/low] Why are hidden fairies coming out more often along with the dragon?
     carried | prior

## thread_5 Ingrid and Warwick (Dunk's deal) [earlier/open] parent=None
   The party plans to carry out Dunk's scheme with Ingrid after the Barrow, but it has not been done.
 - fact_11 owe [high/medium] Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion.
     carried | prior

## thread_6 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Dr. Uriah reached the Barrow Mound but did no penance and made no donation; still owed.
 - fact_12 owe [medium/high] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_13 owe [medium/medium] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior

## thread_7 Squints' share of the treasure [earlier/open] parent=None
   The party gathered its first treasure, but Squints has not yet made his promised second pick.
 - fact_14 owe [medium/high] The party must let Squints pick second from the first treasure, after the elite members. That treasure has now been gathered in the Barrow Mound, but Squints has not yet made his pick.
     updated | prior, beat_21, beat_28, beat_48, beat_58
 - fact_17 could_use [medium/high] From the Barrow Mound the party holds a jewel-encrusted ceremonial dagger (Dr. Uriah values it at upwards of 200 gold in a major city), seven gold candleholders worth 50 gold each, a skull with gold teeth worth 20 gold and five urns worth 100 gold each.
     new | beat_21, beat_28, beat_48, beat_58

## thread_8 Drop Dead Ned's hire [new/open] parent=None
   The party hired Ned under an ongoing arrangement paying them for murders and bodies, and he has offered a deal on the goblin corpses that would need sneaking past the goblins.
 - fact_18 could_use [medium/high] Drop Dead Ned, the inn's killer who carries a little killer wasp, is hired by the party for a 100 gold fee and accompanies them in the Barrow Mound as a scout and killer.
     new | beat_1, beat_12
 - fact_19 could_use [medium/medium] Ned pays the party 10 gold each time they let him murder somebody, provided he can do whatever he wants with the body.
     new | beat_1
 - fact_20 could_use [low/medium] Ned offers 5 gold per goblin body for the three dead goblins in the Barrow Mound's lower corridor, if the party gives him the bodies.
     new | beat_40, beat_41
 - fact_21 blocked_by [medium/medium] The Free Goblin Society goblins would not want their dead compatriots defiled, so giving the goblin bodies to Ned means sneaking them past the goblins.
     new; learned; also thread_10 | beat_42

## thread_9 Protection against the black dragon's poison [new/open] parent=thread_2
   Sir Phidipaldi's plan states that protection from the witch or alchemist is needed because the black dragon is poisonous, so it serves the dragon hunt.
 - fact_22 want [high/medium] Obtain protection against the black dragon's poison before going after the dragon.
     new; also thread_2 | beat_3
 - fact_23 could_use [medium/medium] Sir Phidipaldi's plan is to get the poison protection from the witch or the alchemist once the party returns to town; the cost and whether either can provide it are not yet known.
     new | beat_3

## thread_10 The Free Goblin Society bargain [new/open] parent=None
   The party promised to clear the evil from the mound and keep the goblins' presence from King Hogboon in return for their home there; the evil is not yet cleared.
 - fact_24 owe [high/high] The party promised the Free Goblin Society to clear the evil out of the Barrow Mound, in return for the goblins living there and letting the party take Sir Brandon's goods.
     new | beat_18
 - fact_25 owe [medium/low] The party promised the Free Goblin Society never to tell King Hogboon that the goblins are settled in the Barrow Mound.
     new; no definite end | beat_17, beat_18
 - fact_26 blocked_by [high/high] The undead giant swordsman who killed many of the goblins stands in the way of clearing the evil from the Barrow Mound.
     new; about thread_11 | beat_26, beat_62
 - fact_27 unknown [low/medium] What is making the scratching sounds at the far west end of the mound's lower hunters' corridor?
     new; learned; also thread_11 | beat_43

## thread_11 The undead giant in the Barrow Mound [new/open] parent=None
   A huge undead swordsman, apparently one of Brandon's companions, has killed many goblins and has just appeared in the tomb doorway (beat_62); the danger is live.
 - fact_28 threat [high/high] A seven-foot undead brown skeleton in rusted armor and a mustachioed death mask, dragging a huge greatsword, has appeared in the doorway of Sir Brandon's tomb as the party prepares to leave. The goblins say it is one of the mosaic figures, still alive, and that it killed many of their friends; the slime says it is undead and very mad.
     new; learned; also thread_10 | beat_26, beat_40, beat_46, beat_62
 - fact_29 unknown [medium/medium] Is the undead giant swordsman Alfred, the shaggy giant with a greatsword who was Sir Brandon's companion in the mosaics?
     new; learned | beat_10, beat_26, beat_62

## thread_12 The robes of Saint Arthur [new/open] parent=None
   Dr. Uriah wears the holy robes untested for magic, over Brother Dirk's deep offense; both the robes' nature and Dirk's grievance remain open.
 - fact_30 unknown [medium/medium] Do the robes of Saint Arthur have any magical properties? Dr. Uriah judged them not cursed but could not test them without Ingrid's witch powder, and wearing them had no notable effect.
     new; learned | beat_30, beat_32
 - fact_31 could_use [low/medium] Dr. Uriah wears the robes of Saint Arthur and carries the quarterstaff found with them. Brother Dirk says the robes are far too holy to wear and is deeply offended that Uriah wears them.
     new | beat_30, beat_31, beat_32, beat_33

## thread_13 The noblewoman statue [new/open] parent=None
   The riddle was answered, but whom the speaking noblewoman statue depicts remains an unanswered question.
 - fact_32 unknown [low/low] Whom does the stone noblewoman statue before Sir Brandon's tomb depict, and whose female voice asked the party "What makes a true knight?" Brother Dirk does not know, and the mosaics show neither Wyllt nor Myrddin as a woman.
     new; learned | beat_50, beat_51, beat_52

## thread_14 Brother Dirk's claim on the chalice [new/open] parent=None
   Dirk suggested the jeweled chalice belongs to the church and Trout deferred the question until later.
 - fact_33 could_use [medium/medium] Trout holds the jeweled chalice taken from Sir Brandon's tomb, worth 600 gold.
     new; also thread_7 | beat_56
 - fact_34 unknown [medium/medium] Brother Dirk suggests the jeweled chalice was surely a gift to the church. Does it belong to the church, and will the party give it up? Trout deferred the question until later.
     new; also thread_7 | beat_56

standalone: [{'beat': 'beat_6', 'reason': "The recently opened door was a notable clue, explained by the goblins' arrival."}, {'beat': 'beat_11', 'reason': 'The real gemstones in the mosaics are a notable potential source of wealth.'}, {'beat': 'beat_23', 'reason': "Squints killed the gray ooze and was praised as Trout's apprentice."}, {'beat': 'beat_34', 'reason': "The four virtue statues supplied the answers to the tomb's riddle."}, {'beat': 'beat_38', 'reason': 'Sir Phidipaldi was blessed with good fortune for the rest of the Barrow Mound adventure.'}]
