
## thread_1 Treasure map [earlier/open] parent=None
   Not touched this Session; the Barrow Mound treasure is not tied to the map.
 - fact_1 want [medium/medium] Find the treasure marked on the party's map.
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
 - fact_6 could_use [high/high] Sir Phidipaldi now holds Sir Brandon's magic sword, uncursed, of silvery white metal etched "All shadows yield to my light"; Father William says it is the only weapon that can kill the dragon.
     updated; learned; also thread_10 | prior, beat_59, beat_60, beat_61
 - fact_7 could_use [medium/medium] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     carried; also thread_5 | prior
 - fact_8 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_15 could_use [medium/medium] Sir Phidipaldi plans to show Sir Brandon's sword to Eric the Reeve as proof of competence to press him for an advance on the bounty, to pay Lady Hilda and henchmen.
     new | beat_3
 - fact_16 could_use [medium/low] The Barrow Mound mosaics show Sir Brandon killing the old dragon by driving his sword up through the roof of its open mouth.
     new; learned | beat_10, beat_4
 - fact_17 blocked_by [high/high] The undead giant of the Barrow Mound stands in the tomb doorway, blocking the party from leaving with Sir Brandon's sword.
     new; about thread_11 | beat_62

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
     carried | prior, beat_3

## thread_6 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Dr. Uriah reached the Barrow Mound but did no penance and made no donation; still owed.
 - fact_12 owe [medium/high] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_13 owe [low/medium] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior

## thread_7 Squints' share of the treasure [earlier/open] parent=None
   The party gathered its first treasure, but Squints has not yet made his promised second pick.
 - fact_14 owe [medium/high] The party must let Squints pick second from the first treasure, after the elite members.
     carried | prior, beat_21, beat_28, beat_48, beat_58

## thread_8 Drop Dead Ned's hire [new/open] parent=None
   The party hired Ned under an ongoing arrangement paying them for murders and bodies, and he has offered a deal on the goblin corpses that would need sneaking past the goblins.
 - fact_18 could_use [medium/high] Drop Dead Ned, the inn's killer who carries a little killer wasp, is formally hired by the party (fee of 100 gold, about 33 gold each) and is with them in the Barrow Mound, scouting and checking things for them.
     new | beat_1
 - fact_19 could_use [medium/medium] Ned pays the party 10 gold each time they let him murder somebody, provided he can do whatever he wants with the body.
     new | beat_1
 - fact_20 could_use [low/medium] Ned offers 5 gold per body for the three goblins killed in the Barrow Mound's lower corridor; the party must hand the bodies over to him.
     new | beat_41
 - fact_21 blocked_by [medium/medium] The Free Goblin Society would not want their dead compatriots defiled, so giving Ned the goblin bodies means sneaking them past the goblins.
     new; learned; also thread_10 | beat_42

## thread_9 Protection against the black dragon's poison [new/open] parent=thread_2
   Sir Phidipaldi's plan states that protection from the witch or alchemist is needed because the black dragon is poisonous, so it serves the dragon hunt.
 - fact_22 want [high/medium] Obtain protection against the black dragon's poison before going after the dragon.
     new; also thread_2 | beat_3
 - fact_23 could_use [medium/medium] Sir Phidipaldi's plan names the witch or the alchemist as possible sources of protection against the black dragon's poison; the party must visit one of them after returning from the Barrow Mound. Any cost is not yet known.
     new; UNCERTAIN: Play has not established that either the witch or the alchemist can or will provide such protection, or at what price. | beat_3

## thread_10 The Free Goblin Society bargain [new/open] parent=None
   The party promised to clear the evil from the mound and keep the goblins' presence from King Hogboon in return for their home there; the evil is not yet cleared.
 - fact_24 owe [high/high] The party owes the Free Goblin Society the clearing of the evil out of the Barrow Mound, in return for the goblins being allowed to live there.
     new | beat_18
 - fact_25 owe [medium/low] The party promised the Free Goblin Society not to tell King Hogboon that the goblins are living in the Barrow Mound.
     new; no definite end | beat_17, beat_18
 - fact_26 blocked_by [high/high] The undead giant swordsman in the mound stands in the way of clearing the evil from the Barrow Mound for the goblins.
     new; about thread_11 | beat_26, beat_62
 - fact_27 unknown [low/medium] What is making the scratching sounds at the far west end of the Barrow Mound's lower corridor?
     new; learned; also thread_11 | beat_43
 - fact_28 could_use [low/medium] The Free Goblin Society agreed to walk with the party through the Barrow Mound, though they refuse to do violence themselves.
     new | beat_18, beat_24

## thread_11 The undead giant in the Barrow Mound [new/open] parent=None
   A huge undead swordsman, apparently one of Brandon's companions, has killed many goblins and has just appeared in the tomb doorway (beat_62); the danger is live.
 - fact_29 threat [high/high] A seven-foot undead brown skeleton in rusted armor and a mustachioed death mask, dragging a huge greatsword, has appeared in the doorway of Sir Brandon's tomb as the party prepares to leave. The goblins say it killed many of their friends, and the slime in the pool says it is half dead, very mad and undead.
     new; learned; also thread_10 | beat_26, beat_40, beat_46, beat_62
 - fact_30 unknown [medium/medium] The goblins say one of the figures in the antechamber mosaics is still alive, very big with a huge sword. Is the undead giant Alfred, Brandon's shaggy greatsword-wielding companion shown in the mosaics?
     new; learned | beat_10, beat_26, beat_62

## thread_12 The robes of Saint Arthur [new/open] parent=None
   Dr. Uriah wears the holy robes untested for magic, over Brother Dirk's deep offense; both the robes' nature and Dirk's grievance remain open.
 - fact_31 unknown [medium/medium] Do the robes of Saint Arthur have any magical properties? Dr. Uriah judged them not cursed, but could not test them without Ingrid's witch powder.
     new | beat_30, beat_32
 - fact_32 could_use [low/medium] Dr. Uriah wears the robes of Saint Arthur, holy robes of a saint of this world, and carries the quarterstaff found with them. Wearing them has had no notable effect so far.
     new; learned | beat_30, beat_32
 - fact_33 unknown [low/low] Brother Dirk says the robes are far too holy to wear and is deeply offended that Dr. Uriah wears them. Will Dirk or his church seek to reclaim the robes or hold it against the party?
     new | beat_30, beat_31, beat_33

## thread_13 The noblewoman statue [new/open] parent=None
   The riddle was answered, but whom the speaking noblewoman statue depicts remains an unanswered question.
 - fact_34 unknown [low/low] Whom does the speaking stone noblewoman statue guarding Sir Brandon's tomb depict? Her voice asked "What makes a true knight?", Brother Dirk did not know her, and the mosaics show that neither Wyllt nor Myrddin was a woman.
     new; learned | beat_50, beat_51, beat_52

## thread_14 Brother Dirk's claim on the chalice [new/open] parent=None
   Dirk suggested the jeweled chalice belongs to the church and Trout deferred the question until later.
 - fact_35 could_use [medium/medium] Trout holds the jeweled chalice taken from Sir Brandon's tomb, worth 600 gold.
     new; also thread_7 | beat_56
 - fact_36 unknown [medium/medium] Brother Dirk suggests the jeweled chalice was a gift to the church, and Trout said they would figure it out later. Does the chalice rightfully go to the church, and will the party give it up?
     new | beat_56

standalone: [{'beat': 'beat_6', 'reason': "The recently opened door was a notable clue, explained by the goblins' arrival."}, {'beat': 'beat_11', 'reason': 'The real gemstones in the mosaics are a notable potential source of wealth.'}, {'beat': 'beat_23', 'reason': "Squints killed the gray ooze and was praised as Trout's apprentice."}, {'beat': 'beat_34', 'reason': "The four virtue statues supplied the answers to the tomb's riddle."}, {'beat': 'beat_38', 'reason': 'Sir Phidipaldi was blessed with good fortune for the rest of the Barrow Mound adventure.'}]
