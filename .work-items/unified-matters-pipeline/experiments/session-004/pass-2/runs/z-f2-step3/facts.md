
## thread_1 Treasure map [earlier/changed] parent=None
   Dr. Uriah can now read the map's labels, the map's source is identified as Bral, and Grimny says the treasure is probably hidden at the Dragon's Lair (beat_77), which partly answers where it is. The treasure is not yet found.
 - fact_1 want [high/medium] Find the treasure marked on the party's map.
     carried | prior
 - fact_20 could_use [medium/high] Dr. Uriah can now read languages, letting him read the label under one location on the treasure map per day.
     new | beat_17, beat_18, beat_20
 - fact_21 could_use [high/medium] Grimny's ghost says his brother Bral, the dwarf the party won the map from in a gambling bet, probably hid the dwarves' mine hoard at the cave labeled "Dragon's lair" on the map.
     new; learned; also thread_2,thread_16 | beat_74, beat_75, beat_77
 - fact_22 blocked_by [high/medium] The dragon the party is hunting is tied to the Dragon's Lair, where the treasure is probably hidden, and stands in the way of retrieving it.
     new; UNCERTAIN: Dunk suspects there is no dragon and that Bral only pretends there is one (beat_78).; about thread_2 | beat_18, beat_77, beat_78
 - fact_23 unknown [low/high] What is the one still-unidentified location marked on the treasure map? Sir Phidipaldi guesses it is King Hogboon's.
     new; learned | beat_20, beat_64, beat_65

## thread_2 Dragon hunt (Eric the Reeve's bounty) [earlier/changed] parent=None
   Vivian's faun-wine method gives a way past the impenetrable scales (beat_48, beat_50), and Lady Hilda and Malzazarik joined (beat_62). Dunk now suspects there may be no dragon at all (beat_78). The dragon is still not killed.
 - fact_2 want [high/medium] Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty.
     carried | prior
 - fact_3 blocked_by [high/medium] George says nothing pierces the black dragon's scales; arrows and swords have all failed against them.
     carried | prior
 - fact_4 threat [high/medium] George says the black dragon will soon fly and doom Brandonsford.
     carried | prior
 - fact_5 could_use [medium/low] Lady Hilda will join the party against the dragon if they pay her.
     ended; ENDED: used up: Lady Hilda joined the party, paid with Cedric's promissory note; about thread_12 | prior, beat_62
 - fact_6 could_use [medium/low] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     ended; ENDED: used up: Warwick lent the shirt to the party and Wayman wears it; about thread_13 | prior, beat_35, beat_36
 - fact_7 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_24 could_use [high/high] The party holds Sir Brandon's sword, a magic sword especially effective against evil beings.
     new; learned; also thread_4 | beat_3, beat_16
 - fact_25 could_use [high/high] Vivian says enough faun wine would knock the dragon out so the party can drag Sir Brandon's sword through its mouth, as Sir Brandon did; they must reach its mouth, and dragons move around a lot. The party already has enough faun wine.
     new; learned | beat_47, beat_48, beat_63
 - fact_26 could_use [medium/high] Sir Phidipaldi's plan: catch game, dose it with faun wine, leave it outside the dragon's cave and go in once the dragon has eaten it.
     new | beat_50
 - fact_27 could_use [high/high] The wizard Malzazarik and Lady Hilda have joined the party for the dragon hunt.
     new; also thread_12 | beat_62
 - fact_28 could_use [high/high] The party's treasure map marks the "Dragon's lair"; Grimny says that cave is very small, just one big room, and the dwarves scouted it several times and found it empty.
     new; learned; also thread_1 | beat_18, beat_77
 - fact_29 unknown [high/medium] Is there really a dragon, or, as Dunk speculates, is Bral pretending there is one to keep everybody away from the Dragon's Lair?
     new; also thread_1 | beat_77, beat_78
 - fact_30 unknown [low/medium] Vivian says only Sir Brandon himself told his tale and the church knows it. What did Sir Brandon really do to kill his dragon?
     new; learned | beat_49, beat_53

## thread_3 The goblins' bargain [earlier/changed] parent=None
   Wayman renegotiated with the same goblins. They will stay in the upper rooms behind walled-off stairs instead of having the mound cleared (beat_13). The party now owes Snurk silence toward King Hogboon (beat_15).
 - fact_8 want [medium/low] Clear the evil out of the Barrow Mound for the Free Goblin Society.
     ended; ENDED: replaced: Wayman renegotiated, and the goblins agreed to settle in the church, antechamber and statue room behind walled-off stairs instead of having the mound cleared | prior, beat_11, beat_13
 - fact_9 blocked_by [low/low] A huge undead with a greatsword in the Barrow Mound stands in the way (see thread_4).
     ended; ENDED: no longer relevant: the bargain no longer requires clearing the mound; about thread_4 | prior, beat_10, beat_13
 - fact_31 owe [high/low] Wayman promised Snurk the Walkout that he will never tell King Hogboon where the Free Goblin Society's goblins are living.
     new; no definite end | beat_15
 - fact_32 threat [medium/medium] The goblins settling in the Barrow Mound's upper rooms intend to destroy its church, declaring it job number one of any free state, after Wayman said they could.
     new; also thread_9 | beat_14

## thread_4 Sir Alfred, the undead in the Barrow Mound [earlier/changed] parent=None
   Sir Alfred was incapacitated but not destroyed, and the party left him in the mound (beat_7, beat_10), so the danger has changed in nature but not ended. Brother Dirk calls him holy (beat_9).
 - fact_10 threat [low/low] The skeleton in the tomb doorway may attack the party.
     ended; ENDED: no longer relevant: the skeleton, Sir Alfred, attacked and was incapacitated by Drop Dead Ned's wasp; his remaining danger is fact_11 | prior, beat_7, beat_10
 - fact_11 threat [medium/low] Sir Alfred lies incapacitated but not destroyed in the Barrow Mound's lower level; if he recovers, he may again kill Free Goblin Society members, who are staying in the mound.
     updated; UNCERTAIN: Play never says whether or when Sir Alfred could recover from being broken apart.; also thread_3 | prior, beat_7, beat_10, beat_11
 - fact_12 unknown [low/low] Why does Sir Alfred, a seven-foot undead knight that Brother Dirk regards as holy, roam the Barrow Mound?
     updated; learned | prior, beat_1, beat_9

## thread_5 Missing shipments [earlier/changed] parent=None
   Cedric and Warwick both say supplies stopped when the dragon troubles began, which partly answers why the shipments stopped.
 - fact_13 unknown [medium/low] Cedric says his supply shipments have not reached Brandonsford since the dragon troubles began. What exactly is stopping the shipments, and is the dragon really the cause?
     updated; learned; also thread_2 | prior, beat_24
 - fact_33 unknown [medium/low] Will the supply caravans to Brandonsford flow again, and when?
     new; also thread_12 | beat_24, beat_25

## thread_6 Fairies appearing more often [earlier/open] parent=None
   Not touched this Session.
 - fact_14 unknown [low/low] Why are hidden fairies coming out more often along with the dragon?
     carried | prior

## thread_7 The noblewoman statue [earlier/open] parent=None
   Not touched this Session.
 - fact_15 unknown [low/low] Who does the noblewoman statue in the Barrow Mound depict?
     carried | prior

## thread_8 Ingrid and Warwick (Dunk's deal) [earlier/changed] parent=None
   Ingrid's night visits to Warwick were confirmed, and Sir Phidipaldi told her Warwick is not interested (beat_58), which changes the situation. Dunk's promise to help her was never released, so the thread stays open.
 - fact_16 owe [medium/low] Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion.
     carried; MOOT? Sir Phidipaldi told Ingrid that Warwick knows of her night visits and is not interested, and she left crestfallen (beat_58, beat_60); Ingrid never released Dunk. | prior, beat_58, beat_60
 - fact_34 unknown [medium/low] Ingrid is Warwick's secret night visitor, though Warwick blames the Clurichen. Will she stop visiting him now that Sir Phidipaldi has told her Warwick is not interested?
     new; learned; also thread_13 | beat_30, beat_31, beat_58, beat_59, beat_60

## thread_9 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Dr. Uriah did neither the penance nor the donation. The goblins now intend to destroy the Barrow Mound church (beat_14), which bears on the upkeep he owes.
 - fact_17 owe [medium/medium] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_18 owe [medium/high] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior
 - fact_35 blocked_by [medium/medium] The goblins now settling the Barrow Mound intend to destroy its church, which stands in the way of Dr. Uriah's penance there and the upkeep his donation is meant for.
     new; about thread_3 | beat_14

## thread_10 Squints' share of the treasure [earlier/open] parent=None
   The party took a lot of treasure and signed it over to Cedric (beat_26) without giving Squints a pick. The promise is still owed.
 - fact_19 owe [medium/medium] The party must let Squints pick second from the first treasure, after the elite members.
     carried; MOOT? The barrow treasure was signed over to Cedric for a promissory note (beat_26), and the note was offered to recruit Malzazarik and Lady Hilda (beat_62); Squints never got a pick and was never released.; also thread_12 | prior, beat_16, beat_26

## thread_11 Robes for Brother Dirk [new/open] parent=None
   Dr. Uriah promised to return the barrow robes to the church once the dragon is defeated (beat_23), and that promise is still owed. The promise is to Dirk's church, not a means of the hunt.
 - fact_36 owe [medium/low] Dr. Uriah must give the barrow robes back to Brother Dirk's church once the dragon is defeated; until then he keeps them in case they help against it. Witch powder showed the robes are not magical, only a religious relic.
     new; also thread_2 | beat_16, beat_22, beat_23, beat_40

## thread_12 Cedric's promissory note [new/open] parent=None
   Cedric owes 975 gold for the treasure once the caravans flow again, and the note has been offered to pay the new hirelings. One deal with one counterpart.
 - fact_37 could_use [high/low] Cedric signed a promissory note to pay the party 975 gold for the barrow treasure (three-quarters price), payable once the caravans flow again and he can truck the goods to town.
     new | beat_25, beat_26
 - fact_38 owe [medium/low] The party owes the wizard Malzazarik and Lady Hilda payment out of Cedric's promissory note for joining the party.
     new; UNCERTAIN: Play never stated whether the note was handed over or pledged, or how it is split between the two hirelings.; also thread_2 | beat_28, beat_62
 - fact_39 blocked_by [medium/low] Cedric's note pays nothing until the caravans flow again, which blocks paying Malzazarik and Lady Hilda from it.
     new; about thread_5 | beat_26

## thread_13 The Warwick deal [new/open] parent=None
   The party owes Warwick metal from the Dwarven mine and the return of his mithril shirt, and Warwick holds the lyre and plate armor as collateral. These are sides of one bargain. The shirt was wanted for the mine, not the dragon, so the thread has no parent.
 - fact_40 owe [high/medium] The party must bring Warwick the smith metal from the Dwarven mine. Warwick, out of metal since the dragon appeared, holds Sir Phidipaldi's lyre and the party's plate armor as collateral until then.
     new; also thread_5 | beat_27, beat_33, beat_34, beat_35
 - fact_41 owe [high/medium] The party must return Warwick's mithril chain shirt, lent for the Dwarven mine trip. Ingrid says it was his grandfather's armor and he never let her touch it.
     new; also thread_2 | beat_34, beat_35, beat_57
 - fact_42 could_use [medium/high] Wayman wears Warwick's mithril chain shirt, on loan, over his leather armor; it greatly improves his protection and halves damage from magic weapons and spells.
     new; also thread_2 | beat_35, beat_36
 - fact_43 blocked_by [high/high] A cave-in seals the Dwarven mine entrance, blocking access to the metal owed to Warwick. It looks natural and can be dug through; Dunk has started breaking into it, uncovering a dead dwarf.
     new; learned; also thread_16 | beat_67, beat_68

## thread_14 Protection against the dragon's poison [new/open] parent=thread_2
   Sir Phidipaldi said anti-poison remedies are needed because they are hunting the dragon (beat_37), which makes this a child of the hunt. Neither Ingrid nor Vivian could provide any (beat_51).
 - fact_44 want [medium/low] Obtain protection against the dragon's poison before facing the dragon.
     new; also thread_2 | beat_37, beat_42
 - fact_45 blocked_by [medium/low] No source of protection against the dragon's poison is known. Ingrid says it is powerful magic beyond her as an apprentice, and Vivian, the witch of the wood, privately admits she knows only three potions and offered nothing against the venom.
     new; learned | beat_42, beat_51

## thread_15 Vivian's message to Grimny [new/resolved] parent=None
   Dunk delivered Vivian's scent and letter to Grimny's ghost, who then ascended (beat_79, beat_81). Nothing remains owed.

## thread_16 Who killed Grimny [new/open] parent=None
   Grimny believes his brother Bral killed him (beat_72), but this is unconfirmed. The fate of the other dwarves is also unknown. The question stands apart from the treasure hunt's aim.
 - fact_46 unknown [high/medium] Grimny's ghost believed his brother Bral, the greediest of the seven dwarf brothers, killed him. Did Bral kill Grimny, and how?
     new; learned | beat_72, beat_68
 - fact_47 unknown [medium/low] What became of the other dwarf brothers who worked the Dwarven mine: Grelli, Durney, Brenny, Tedry, Rooney and Bral?
     new; learned | beat_72, beat_67

## thread_17 Grimny's ring [new/open] parent=None
   Dunk wears a magical ring that drew him to put it on, and no one knows whether it is cursed (beat_69, beat_70). Its known power to reach Grimny's ghost is now moot because the ghost has gone.
 - fact_48 unknown [high/medium] Dunk wears the magical ring taken from Grimny's body, which drew him with a growing urge to put it on. Is the ring cursed?
     new; learned | beat_68, beat_69, beat_70
 - fact_49 unknown [medium/low] The ring's only known power was letting its wearer see and speak with Grimny's ghost, and the ghost has since ascended. Does the ring do anything else now?
     new; learned | beat_71, beat_81

standalone: [{'beat': 'beat_38', 'reason': "Ingrid's wares, including wolfsbane, witch powder and mandrake tea, are now known as a resource the party can buy."}]
