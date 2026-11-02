
## thread_1 Treasure map [earlier/changed] parent=None
   Dr. Uriah can now read the map's labels, and the unmarked location proved to be King Hogboon's ruins. Grimny revealed the map came from Bral and the treasure is probably hidden at the Dragon's Lair (beat_74, beat_77), so the question is partly answered while the treasure is still unfound.
 - fact_1 want [high/high] Find the treasure marked on the party's map.
     carried | prior
 - fact_20 could_use [high/high] Grimny's ghost said Bral probably hid the dwarves' hoard in the cave marked "Dragon's lair" on the party's map. The dwarves had scouted it as a hiding spot: very small, just one big room, a place nobody goes.
     new; learned; also thread_2 | beat_74, beat_75, beat_77
 - fact_21 could_use [medium/high] Dr. Uriah can read one label on the party's map per day. The map, which came from Bral, marks the Dragon's lair, the Dwarven mine and King Hogboon's temple ruins.
     new; learned; also thread_2 | beat_17, beat_18, beat_20, beat_65, beat_75
 - fact_22 blocked_by [medium/medium] The dragon reported to live at the Dragon's lair stands between the party and the treasure believed to be hidden there.
     new; about thread_2; also thread_2 | beat_18, beat_77

## thread_2 Dragon hunt (Eric the Reeve's bounty) [earlier/changed] parent=None
   The impenetrable scales now have a stated workaround: knock the dragon out with faun wine and drag Sir Brandon's sword through its mouth (beat_48, beat_50). Lady Hilda joined and the lair is identified, but Grimny's account of an empty cave makes Dunk suspect there is no dragon (beat_77, beat_78).
 - fact_2 want [high/medium] Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty.
     carried | prior
 - fact_3 blocked_by [high/high] George says nothing pierces the black dragon's scales; arrows and swords have all failed. Vivian says enough faun wine would knock the dragon out so Sir Brandon's sword can be dragged through its mouth, but they must reach its mouth and dragons move around a lot.
     updated; learned | prior, beat_48, beat_63
 - fact_4 threat [medium/low] George says the black dragon will soon fly and doom Brandonsford.
     carried | prior
 - fact_5 could_use [low/low] Lady Hilda will join the party against the dragon if they pay her.
     ended; ENDED: used up: Lady Hilda joined the party, recruited with Cedric's promissory note; about thread_12 | prior, beat_62
 - fact_6 could_use [low/low] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     ended; ENDED: used up: Warwick lent the shirt to the party under the Warwick deal; about thread_13 | prior, beat_35
 - fact_7 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_23 unknown [high/high] Grimny says the dwarves found the map's Dragon's Lair cave empty when scouting it. Is there really a dragon, or is Bral faking one to keep people away, as Dunk suspects?
     new; learned; also thread_1 | beat_77, beat_78
 - fact_24 could_use [high/high] The party holds Sir Brandon's magic sword, which is especially effective against evil beings.
     new; learned | beat_3, beat_16
 - fact_25 could_use [medium/high] Sir Phidipaldi's plan: catch game, dose it with Dunk's faun wine, leave it outside the dragon's cave and go in once the dragon has eaten it.
     new | beat_47, beat_50, beat_63

## thread_3 The goblins' bargain [earlier/changed] parent=None
   The deal was renegotiated: instead of a cleared mound, the goblins will wall off the stairs and hold the church, antechamber and statue room (beat_13). Wayman's new promise never to reveal their whereabouts to King Hogboon remains owed (beat_15).
 - fact_8 want [medium/low] Clear the evil out of the Barrow Mound for the Free Goblin Society.
     ended; ENDED: replaced: the deal was renegotiated so the goblins will wall off the stairs and hold the church, antechamber and statue room instead of a cleared mound | prior, beat_10, beat_11, beat_13
 - fact_9 blocked_by [low/low] A huge undead with a greatsword in the Barrow Mound stands in the way (see thread_4).
     ended; ENDED: no longer relevant: the goblins no longer need the mound cleared and will wall off the stairs; about thread_4 | prior, beat_10, beat_13
 - fact_26 owe [medium/low] Wayman has promised Snurk and the Free Goblin Society never to tell King Hogboon where the goblins are.
     new; no definite end | beat_15

## thread_4 Sir Alfred, the undead in the Barrow Mound [earlier/changed] parent=None
   Sir Alfred was incapacitated but not destroyed, and the party left him that way (beat_7, beat_10), so the danger continues in a changed form. The goblins plan to wall him off, and Brother Dirk regards him as holy.
 - fact_10 threat [medium/low] Sir Alfred, the seven-foot undead knight with a great sword, lies broken apart and incapacitated but not destroyed in the Barrow Mound, and may recover to attack anyone who returns there.
     updated | prior, beat_1, beat_5, beat_7, beat_10
 - fact_11 threat [low/low] Sir Alfred, who killed the Free Goblin Society's companions, may kill more of the goblins now settling in the Barrow Mound if he recovers and their wall over the stairs fails.
     updated; also thread_3 | prior, beat_10, beat_11, beat_13
 - fact_12 unknown [low/low] Why does the undead knight Sir Alfred roam the Barrow Mound, and why does Brother Dirk regard him as holy?
     updated | prior, beat_1, beat_9

## thread_5 Missing shipments [earlier/open] parent=None
   Cedric and Warwick say shipments and metal stopped when the dragon appeared, but why they stopped is still unexplained.
 - fact_13 unknown [medium/medium] Cedric says his supply shipments have not come in since the dragon troubles began, and Warwick has had no metal for weeks since the dragon appeared. Why have shipments stopped reaching Brandonsford?
     updated; learned; also thread_12,thread_13 | prior, beat_24, beat_27, beat_33

## thread_6 Fairies appearing more often [earlier/open] parent=None
   Not touched this Session.
 - fact_14 unknown [medium/low] Why are hidden fairies coming out more often along with the dragon?
     carried | prior

## thread_7 The noblewoman statue [earlier/open] parent=None
   Not touched this Session.
 - fact_15 unknown [low/low] Who does the noblewoman statue in the Barrow Mound depict?
     carried | prior

## thread_8 Ingrid and Warwick (Dunk's deal) [earlier/changed] parent=None
   Warwick's night visitor is revealed as Ingrid, and Sir Phidipaldi told her Warwick knows and is not interested (beat_58, beat_59), which changes the situation's shape. Dunk's promise to help her was never released, so the thread stays open.
 - fact_16 owe [medium/medium] Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion.
     carried; MOOT? Sir Phidipaldi told Ingrid that Warwick knows about her night visits and is not interested, and she left crestfallen (beat_58, beat_60); Ingrid never released Dunk. | prior, beat_58, beat_59, beat_60

## thread_9 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Not touched this Session; the penance and donation are still owed.
 - fact_17 owe [medium/medium] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_18 owe [medium/high] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior

## thread_10 Squints' share of the treasure [earlier/open] parent=None
   The party took a lot of treasure from the barrow and signed it over to Cedric for a promissory note (beat_26). Squints has not been given second pick, so the promise is still owed.
 - fact_19 owe [medium/medium] The party must let Squints pick second from the first treasure, after the elite members.
     carried | prior, beat_16
 - fact_27 blocked_by [medium/low] The party's first treasure, the barrow haul, was signed over to Cedric for a promissory note, so it is not available for Squints to pick from. This blocks the party's promise to give Squints second pick.
     new; about thread_12; also thread_12 | beat_16, beat_25, beat_26

## thread_11 Robes for Brother Dirk [new/open] parent=None
   Dr. Uriah promised to return the barrow robes to the church once the dragon is defeated (beat_23); the robes proved non-magical, and the promise is still outstanding.
 - fact_28 owe [medium/low] Dr. Uriah must give the barrow robes back to the church (Brother Dirk) once the dragon is defeated; until then he keeps them. Witch powder showed the robes are not magical, only a religious relic.
     new | beat_21, beat_22, beat_23, beat_39, beat_40

## thread_12 Cedric's promissory note [new/open] parent=None
   Cedric owes 975 gold for the treasure once the caravans flow again, and the note was used to recruit Malzazarik and Lady Hilda (beat_62). Payment is still pending.
 - fact_29 could_use [high/low] Cedric's signed promissory note obliges him to pay the party 975 gold (three-quarters price) for the barrow treasure once the caravans flow again. Sir Phidipaldi has pledged the note to recruit Malzazarik and Lady Hilda.
     new; UNCERTAIN: Unclear whether the party still holds the note or has handed it, or its proceeds, to Malzazarik and Lady Hilda.; about thread_5; also thread_2 | beat_25, beat_26, beat_28, beat_62

## thread_13 The Warwick deal [new/open] parent=None
   This is one bargain: Warwick keeps the lyre and holds the plate armor as collateral, and the party borrows his heirloom mithril shirt in exchange for bringing metal from the Dwarven mine. The mine is blocked by a cave-in, and the metal has not been delivered.
 - fact_30 owe [high/medium] The party must bring metal from the Dwarven mine to Warwick the smith in exchange for the loan of his mithril chain shirt. Meanwhile Warwick keeps Sir Phidipaldi's lyre and holds the party's plate armor as collateral.
     new | beat_33, beat_34, beat_35
 - fact_31 could_use [high/high] Wayman wears Warwick's mithril chain shirt, on loan under the deal and due back to Warwick. It greatly improves his protection and halves damage from magic weapons and spells. Ingrid says it was Warwick's grandfather's armor and he never let anyone touch it.
     new | beat_35, beat_36, beat_57
 - fact_32 blocked_by [high/high] A cave-in seals the Dwarven mine entrance and blocks getting metal for Warwick. It looks natural and can be dug through; Dunk has started breaking into it.
     new; learned; also thread_16 | beat_67, beat_68

## thread_14 Protection against the dragon's poison [new/open] parent=thread_2
   Sir Phidipaldi said they needed anti-poison remedies because they are hunting the dragon (beat_37), so this serves the dragon hunt. Neither Ingrid nor Vivian could supply any (beat_42, beat_51).
 - fact_33 want [medium/low] Obtain protection against the dragon's poison, which George the Hunter reported, before facing the dragon.
     new; also thread_2 | beat_37, beat_42
 - fact_34 blocked_by [medium/low] No known source can supply protection against the dragon's poison: Ingrid says it is powerful magic beyond her as an apprentice, and Vivian, the witch of the wood, privately admits she knows only three potions and offered nothing against the venom.
     new; learned | beat_42, beat_51

## thread_15 Vivian's message to Grimny [new/resolved] parent=None
   Vivian asked the party to deliver her note and scent to Grimny, and Dunk delivered both to his ghost. Grimny ascended elated, so nothing more is owed (beat_79, beat_81).

## thread_16 Who killed Grimny [new/open] parent=None
   Grimny's ghost, reached through the ring, said his greedy brother Bral killed him, and the party's map came from Bral. Grimny has departed, but Bral and the murder remain unaddressed.
 - fact_35 unknown [high/medium] Grimny's ghost says his greedy brother Bral killed him. Did Bral really murder Grimny, and why?
     new; learned | beat_72, beat_74
 - fact_36 unknown [high/low] Where is Bral now? He is the dwarf who lost the treasure map to Sir Phidipaldi and Dr. Uriah in a gambling bet.
     new; learned; also thread_1 | beat_74, beat_75
 - fact_37 unknown [medium/medium] What became of Grimny's other brothers, Grelli, Durney, Brenny, Tedry and Rooney, given the mine's cave-in and the burnt cabin?
     new; learned | beat_67, beat_72
 - fact_38 unknown [medium/medium] Is the magical ring Dunk took from the dead dwarf's hand, which let him see and speak with Grimny's ghost, cursed?
     new; learned | beat_69, beat_70, beat_71

standalone: [{'beat': 'beat_53', 'reason': 'Vivian revealed the church keeps the tale of Sir Brandon and bars her from it, which is background that bears on no open situation.'}]
