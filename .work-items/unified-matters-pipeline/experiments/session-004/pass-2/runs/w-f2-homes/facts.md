
## thread_1 Treasure map [earlier/changed] parent=None
   Dr. Uriah can now read the map's labels, and the unmarked location proved to be King Hogboon's ruins. Grimny revealed the map came from Bral and the treasure is probably hidden at the Dragon's Lair (beat_74, beat_77), so the question is partly answered while the treasure is still unfound.
 - fact_1 want [high/medium] Find the treasure marked on the party's map.
     carried | prior
 - fact_20 could_use [high/medium] Grimny's ghost says the map's treasure is the dwarves' hoard from the mine, which they kept back from selling to the town, and that Bral probably hid it at the place the map labels "Dragon's lair."
     new; learned; about thread_2; also thread_2,thread_16 | beat_74, beat_75, beat_77
 - fact_21 could_use [low/medium] Dr. Uriah can read what is written under one location on the treasure map per day.
     new | beat_17, beat_18, beat_20
 - fact_22 threat [low/low] The map's unmarked location is a ruined temple to a forgotten wild god, now a castle full of King Hogboon's goblins, near the route to the Dwarven mine; parties passing it may be spotted by the goblins.
     new; learned; also thread_3 | beat_20, beat_64, beat_65

## thread_2 Dragon hunt (Eric the Reeve's bounty) [earlier/changed] parent=None
   The impenetrable scales now have a stated workaround: knock the dragon out with faun wine and drag Sir Brandon's sword through its mouth (beat_48, beat_50). Lady Hilda joined and the lair is identified, but Grimny's account of an empty cave makes Dunk suspect there is no dragon (beat_77, beat_78).
 - fact_2 want [high/high] Kill the dragon near Brandonsford for Eric the Reeve's 1000 gold bounty.
     carried | prior
 - fact_3 blocked_by [high/medium] George says nothing pierces the black dragon's scales; arrows and swords have all failed against them.
     carried | prior
 - fact_4 threat [high/medium] George says the black dragon will soon fly and doom Brandonsford.
     carried | prior
 - fact_5 could_use [medium/low] Lady Hilda will join the party against the dragon if they pay her.
     ended; ENDED: used up: Lady Hilda joined the party, paid with Cedric's promissory note | prior, beat_62
 - fact_6 could_use [medium/low] Warwick keeps a magical mithril chain shirt; Dunk says it could help against the dragon.
     ended; ENDED: used up: Warwick lent the party the mithril shirt; now held under the Warwick deal; about thread_13 | prior, beat_35
 - fact_7 unknown [medium/low] Where did the new dragon near Brandonsford come from?
     carried | prior
 - fact_23 could_use [high/high] The party holds Sir Brandon's magic sword, especially effective against evil beings; Vivian says Sir Brandon killed his dragon by dragging it through the dragon's mouth.
     new; learned; also thread_4 | beat_3, beat_16, beat_48
 - fact_24 could_use [high/high] Dunk carries enough faun wine; Vivian says a sufficient amount would knock the dragon out so they can reach its mouth, though she warns dragons move around a lot.
     new; learned | beat_47, beat_48, beat_63
 - fact_25 could_use [medium/high] Sir Phidipaldi's plan: catch game, dose it with faun wine, leave it outside the dragon's cave and go in once the dragon has eaten it.
     new | beat_50
 - fact_26 could_use [high/high] The party's map marks the Dragon's Lair; Grimny says it is a very small cave, just one big room, which the dwarves scouted several times and found empty.
     new; learned; also thread_1 | beat_18, beat_77
 - fact_27 unknown [high/high] Is there really a dragon, or is Bral pretending there is one to keep everybody away from the Dragon's Lair, as Dunk suspects?
     new; also thread_16 | beat_77, beat_78
 - fact_28 could_use [medium/high] The wizard Malzazarik and the warrior Lady Hilda have joined the party for the dragon hunt.
     new; also thread_12 | beat_62
 - fact_29 unknown [low/low] Vivian says Sir Brandon's tale is told only by Sir Brandon himself. What did he and his companions really do to kill his dragon?
     new; learned | beat_49

## thread_3 The goblins' bargain [earlier/changed] parent=None
   The deal was renegotiated: instead of a cleared mound, the goblins will wall off the stairs and hold the church, antechamber and statue room (beat_13). Wayman's new promise never to reveal their whereabouts to King Hogboon remains owed (beat_15).
 - fact_8 want [medium/low] Clear the evil out of the Barrow Mound for the Free Goblin Society.
     ended; ENDED: replaced by fact_new_2: the deal was renegotiated so the goblins wall off the stairs and keep only the upper rooms | prior, beat_11, beat_13
 - fact_9 blocked_by [low/low] A huge undead with a greatsword in the Barrow Mound stands in the way (see thread_4).
     ended; ENDED: no longer relevant: the goblins accepted a new deal that no longer requires clearing the mound; about thread_4 | prior, beat_10, beat_13
 - fact_30 owe [high/low] Wayman promised Snurk of the Free Goblin Society never to tell King Hogboon where the goblins are, should he meet him.
     new; no definite end | beat_15
 - fact_31 could_use [low/low] The Free Goblin Society (Watak, Grimble, Snurk and Peg) are on friendly terms with the party and now hold the Barrow Mound's church, antechamber and statue room, having agreed to wall off the stairs below; they mean to destroy the church as their first act.
     new; also thread_4 | beat_13, beat_14

## thread_4 Sir Alfred, the undead in the Barrow Mound [earlier/changed] parent=None
   Sir Alfred was incapacitated but not destroyed, and the party left him that way (beat_7, beat_10), so the danger continues in a changed form. The goblins plan to wall him off, and Brother Dirk regards him as holy.
 - fact_10 threat [medium/low] Sir Alfred, the undead knight in the Barrow Mound, is incapacitated but not destroyed; he may recover and attack anyone who returns to the mound, the party included.
     updated; also thread_3 | prior, beat_1, beat_5, beat_7, beat_10
 - fact_11 threat [medium/low] If Sir Alfred recovers, he may kill more Free Goblin Society members, who are settling in the Barrow Mound; the goblins say he already killed all their friends down there.
     updated; also thread_3 | prior, beat_10, beat_11, beat_13
 - fact_12 unknown [low/low] Why does Sir Alfred, a seven-foot undead knight with a greatsword and a bronze death mask, roam the Barrow Mound?
     updated | prior, beat_1
 - fact_32 unknown [low/medium] Brother Dirk regards Sir Alfred as holy and would rather the party not destroy him. Why does he consider this undead knight holy?
     new; learned | beat_9

## thread_5 Missing shipments [earlier/open] parent=None
   Cedric and Warwick say shipments and metal stopped when the dragon appeared, but why they stopped is still unexplained.
 - fact_13 unknown [medium/low] Cedric says his supply shipments and Warwick says his metal stopped reaching Brandonsford when the dragon appeared. Why did they stop?
     updated; learned; also thread_12,thread_13 | prior, beat_24, beat_27, beat_33

## thread_6 Fairies appearing more often [earlier/open] parent=None
   Not touched this Session.
 - fact_14 unknown [low/low] Why are hidden fairies coming out more often along with the dragon?
     carried | prior

## thread_7 The noblewoman statue [earlier/open] parent=None
   Not touched this Session.
 - fact_15 unknown [low/low] Who does the noblewoman statue in the Barrow Mound depict?
     carried | prior

## thread_8 Ingrid and Warwick (Dunk's deal) [earlier/changed] parent=None
   Warwick's night visitor is revealed as Ingrid, and Sir Phidipaldi told her Warwick knows and is not interested (beat_58, beat_59), which changes the situation's shape. Dunk's promise to help her was never released, so the thread stays open.
 - fact_16 owe [medium/low] Dunk must help Ingrid get into Warwick's house and give Warwick the sleeping potion.
     carried; MOOT? Sir Phidipaldi told Ingrid that Warwick knows about her night visits and is not interested (beat_58), and she left crestfallen (beat_60); Ingrid never released Dunk. | prior, beat_58, beat_60
 - fact_33 unknown [low/medium] Now that Sir Phidipaldi has told her Warwick knows and is not interested, will Ingrid keep secretly visiting Warwick at night, or still expect Dunk's help?
     new; learned | beat_58, beat_59, beat_60

## thread_9 Dr. Uriah's penance for Father William [earlier/open] parent=None
   Not touched this Session; the penance and donation are still owed.
 - fact_17 owe [medium/medium] Dr. Uriah must do penance at the Barrow Mound for Father William.
     carried | prior
 - fact_18 owe [medium/high] Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep.
     carried | prior

## thread_10 Squints' share of the treasure [earlier/open] parent=None
   The party took a lot of treasure from the barrow and signed it over to Cedric for a promissory note (beat_26). Squints has not been given second pick, so the promise is still owed.
 - fact_19 owe [medium/low] The party must let Squints pick second from the first treasure, after the elite members.
     carried; MOOT? The barrow treasure (beat_16) was signed over to Cedric for a promissory note (beat_26), which was then pledged to recruit Malzazarik and Lady Hilda (beat_62); Squints was never given a pick or released. | prior, beat_16, beat_26, beat_62

## thread_11 Robes for Brother Dirk [new/open] parent=None
   Dr. Uriah promised to return the barrow robes to the church once the dragon is defeated (beat_23); the robes proved non-magical, and the promise is still outstanding.
 - fact_34 owe [medium/low] Dr. Uriah promised Brother Dirk to return the barrow robes to the church once the dragon is defeated. He keeps them until then in case they help against it, though witch powder showed they are a non-magical religious relic.
     new; about thread_2 | beat_21, beat_22, beat_23, beat_39, beat_40

## thread_12 Cedric's promissory note [new/open] parent=None
   Cedric owes 975 gold for the treasure once the caravans flow again, and the note was used to recruit Malzazarik and Lady Hilda (beat_62). Payment is still pending.
 - fact_35 could_use [high/low] Cedric signed a promissory note to pay the party 975 gold for the barrow treasure (three-quarters price), payable once the caravans flow to Brandonsford again.
     new; also thread_10 | beat_25, beat_26
 - fact_36 owe [medium/low] The party pledged Cedric's promissory note to the wizard Malzazarik and Lady Hilda to recruit them, and owes them payment from it once it is paid.
     new; UNCERTAIN: Play never stated how much of the note goes to Malzazarik and Lady Hilda or on what terms.; also thread_2 | beat_28, beat_62

## thread_13 The Warwick deal [new/open] parent=None
   This is one bargain: Warwick keeps the lyre and holds the plate armor as collateral, and the party borrows his heirloom mithril shirt in exchange for bringing metal from the Dwarven mine. The mine is blocked by a cave-in, and the metal has not been delivered.
 - fact_37 owe [high/medium] The party must bring metal from the Dwarven mine back to Warwick the smith, in exchange for the loan of his mithril chain shirt; Warwick holds the party's plate armor (claimed by Sir Phidipaldi to be Sir Brandon's original) as collateral.
     new | beat_32, beat_33, beat_34, beat_35
 - fact_38 owe [high/medium] The party must return Warwick's mithril chain shirt, his grandfather's heirloom armor, which he lent them for the trip to the Dwarven mine.
     new | beat_34, beat_35, beat_57
 - fact_39 could_use [high/high] Wayman wears Warwick's mithril chain shirt over his leather armor (on loan), greatly improving his protection and halving damage from magic weapons and spells.
     new; also thread_2,thread_8 | beat_35, beat_36
 - fact_40 blocked_by [high/high] The entrance of the Dwarven mine, north of town past King Hogboon's goblin ruins, is sealed by a cave-in, blocking access to the metal Warwick wants. It looks natural and can be dug through; Dunk has begun clearing it, uncovering a dead dwarf.
     new; learned; also thread_1,thread_16 | beat_64, beat_67, beat_68

## thread_14 Protection against the dragon's poison [new/open] parent=thread_2
   Sir Phidipaldi said they needed anti-poison remedies because they are hunting the dragon (beat_37), so this serves the dragon hunt. Neither Ingrid nor Vivian could supply any (beat_42, beat_51).
 - fact_41 want [medium/low] Obtain protection against the dragon's poison before facing the dragon.
     new; also thread_2 | beat_37, beat_42
 - fact_42 blocked_by [medium/low] The party has no known source of protection against the dragon's poison. Ingrid says it is powerful magic beyond her as an apprentice. Vivian, the witch of the wood, privately admits she knows only three potions and offered nothing against the venom.
     new; learned; also thread_2 | beat_42, beat_51

## thread_15 Vivian's message to Grimny [new/resolved] parent=None
   Vivian asked the party to deliver her note and scent to Grimny, and Dunk delivered both to his ghost. Grimny ascended elated, so nothing more is owed (beat_79, beat_81).

## thread_16 Who killed Grimny [new/open] parent=None
   Grimny's ghost, reached through the ring, said his greedy brother Bral killed him, and the party's map came from Bral. Grimny has departed, but Bral and the murder remain unaddressed.
 - fact_43 unknown [high/medium] Grimny's ghost believes his brother Bral, the greediest of the seven dwarf brothers, killed him. Did Bral really murder Grimny, and how?
     new; learned | beat_68, beat_72
 - fact_44 unknown [high/medium] Sir Phidipaldi and Dr. Uriah concluded that Bral is the dwarf who lost the party's treasure map to them in a gambling bet. Where is Bral now?
     new; learned; also thread_1,thread_2 | beat_72, beat_74, beat_75
 - fact_45 could_use [medium/low] Dunk has the magic ring taken from a dead dwarf's finger at the Dwarven mine; its wearer could see and speak with Grimny's ghost, though Grimny has since departed.
     new; learned; also thread_15 | beat_69, beat_70, beat_71, beat_81
 - fact_46 unknown [medium/medium] Is the magic ring Dunk put on cursed? Dr. Uriah's witch powder showed it is magical but could not tell, and Dunk felt a growing urge to wear it.
     new; learned | beat_69, beat_70

standalone: [{'beat': 'beat_53', 'reason': 'Vivian revealed the church keeps the tale of Sir Brandon and bars her from it, which is background that bears on no open situation.'}]
