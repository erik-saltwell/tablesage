<eligible_openings>
[
 {
  "thread": "thread_2",
  "id": "fact_5",
  "kind": "could_use",
  "text": "Lady Hilda, a seasoned fighter in chain mail with a shield, offers to join the party for pay to hunt the dragon; she won't go alone.",
  "state": "open",
  "change": "new",
  "ended_how": null,
  "learned_this_session": false,
  "definite_end": null,
  "possibly_moot": null,
  "certainty": "established",
  "uncertain_reason": null,
  "about_thread": null,
  "also_bears_on": [],
  "importance": "medium",
  "actionability": "high",
  "evidence": [
   "beat_9"
  ],
  "classification": {
   "opening_basis": "Trigger: hire Lady Hilda for an unstated fee. Benefit: an experienced armoured fighter added to the dragon hunt, reducing its risk.",
   "opening_type": "enabling",
   "form": "opening",
   "helps_thread": "thread_2",
   "role": "direct",
   "support_basis": "A seasoned fighter adds real combat strength against a dragon that has already maimed a capable woodsman.",
   "goal_support": "medium",
   "action_basis": "Hilda explicitly offered to join a party of adventurers for money, and Sir Phidipaldi said they would come back for her services.",
   "action_supported": "yes",
   "acquired_by_acting_on_opening": false
  },
  "resource_subject": "",
  "classification_change_basis": "",
  "temporary_id": "fact_new_2"
 },
 {
  "thread": "thread_5",
  "id": "fact_14",
  "kind": "could_use",
  "text": "Drop Dead Ned offers himself and his killer wasp for hire at 100 gold a week, doing anything as long as he gets to kill people with the wasp; Dr. Uriah said he would think about it.",
  "state": "open",
  "change": "new",
  "ended_how": null,
  "learned_this_session": false,
  "definite_end": null,
  "possibly_moot": null,
  "certainty": "established",
  "uncertain_reason": null,
  "about_thread": null,
  "also_bears_on": [
   "thread_2"
  ],
  "importance": "medium",
  "actionability": "high",
  "evidence": [
   "beat_10",
   "beat_18",
   "beat_19",
   "beat_20"
  ],
  "classification": {
   "opening_basis": "Trigger: paying Ned 100 gold a week to hire him. Benefit: an extra killer and his wasp, which he uses to kill things fast, added to the party's fighting strength against the dragon the Reeve wants killed.",
   "opening_type": "enabling",
   "form": "opening",
   "helps_thread": "thread_2",
   "role": "direct",
   "support_basis": "Ned adds a willing killer and a fast-killing wasp to a dragon hunt, though nothing established shows the wasp works on a dragon and his condition is killing people.",
   "goal_support": "low",
   "action_basis": "Ned explicitly offered his and the wasp's services for 100 gold a week, and Uriah is weighing it.",
   "action_supported": "yes",
   "acquired_by_acting_on_opening": false
  },
  "resource_subject": "",
  "classification_change_basis": "",
  "temporary_id": "fact_new_1"
 },
 {
  "thread": "thread_7",
  "id": "fact_18",
  "kind": "could_use",
  "text": "Quinn and Sir Phidipaldi have planned a fake ale delivery: Quinn brings bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to the Golden Egg to see who comes for it.",
  "state": "open",
  "change": "new",
  "ended_how": null,
  "learned_this_session": false,
  "definite_end": null,
  "possibly_moot": null,
  "certainty": "established",
  "uncertain_reason": null,
  "about_thread": null,
  "also_bears_on": [],
  "importance": "medium",
  "actionability": "high",
  "evidence": [
   "beat_32"
  ],
  "classification": {
   "opening_basis": "Trigger: staging the showy fake delivery. Benefit: it baits the nightly thief into revealing themselves without risking real stock, which Quinn proposed for exactly this purpose.",
   "opening_type": "enabling",
   "form": "opening",
   "helps_thread": "thread_7",
   "role": "direct",
   "support_basis": "It gives the party a concrete way to draw out and observe whoever takes Quinn's ale, though it is untested whether the thief will take the bait.",
   "goal_support": "medium",
   "action_basis": "Quinn proposed the sting and agreed to supply bottles; Sir Phidipaldi agreed to perform the delivery.",
   "action_supported": "yes",
   "acquired_by_acting_on_opening": false
  },
  "resource_subject": "",
  "classification_change_basis": "",
  "temporary_id": "fact_new_2"
 }
]
</eligible_openings>

<scenes>
[
 {
  "id": "scene_1",
  "location": "Brandonsford's gate",
  "people": {
   "party": [
    "Sir Phidipaldi",
    "Wayman Tisdale",
    "Dr. Uriah",
    "Dunk"
   ],
   "others": [
    "a night watchman"
   ]
  },
  "cue": "\"We claim the sacred law of Zeus for hospitality\" - Sir Phidipaldi",
  "beats": [
   {
    "id": "beat_1",
    "kind": "event",
    "text": "The party arrived at Brandonsford at sunset, following a treasure map whose marked locations they did not recognize; they assumed the treasure lay at one of those locations, though all the surrounding land was unknown to them.",
    "importance": "high",
    "ledger": [
     0,
     2
    ]
   },
   {
    "id": "beat_2",
    "kind": "learned",
    "text": "Brandonsford has no guards or proper law enforcement; a rotating group of able-bodied men keeps the night watch.",
    "importance": "low",
    "ledger": [
     1
    ]
   },
   {
    "id": "beat_3",
    "kind": "event",
    "text": "Challenged by a night watchman, Sir Phidipaldi claimed the sacred law of Zeus for hospitality and Wayman said they came from Ithaca; the watchman let them in and pointed out the two inns.",
    "importance": "low",
    "ledger": [
     4,
     5,
     6,
     7,
     8
    ]
   },
   {
    "id": "beat_4",
    "kind": "learned",
    "text": "Brandonsford has a general store, a smith, a small church, an alchemist shop and a farm on the edge of town; the Clumsy Fox Tavern is busy and warm, while the Golden Egg Tavern across the street has fewer people.",
    "importance": "low",
    "ledger": [
     8,
     9
    ]
   }
  ]
 },
 {
  "id": "scene_2",
  "location": "The river",
  "people": {
   "party": [
    "Dr. Uriah"
   ],
   "others": [
    "Reginald the Frog"
   ]
  },
  "cue": "Asking Reginald the frog which tavern is better",
  "beats": [
   {
    "id": "beat_5",
    "kind": "event",
    "text": "Dr. Uriah used his once-daily power to speak with aquatic animals at the river and asked a frog named Reginald which tavern was better; Reginald did not know.",
    "importance": "low",
    "ledger": [
     10,
     11,
     12,
     13
    ]
   },
   {
    "id": "beat_6",
    "kind": "learned",
    "text": "Reginald says a little trickster creature called a Clurichen comes from the riverbanks into town every night, up to no good, and that wherever it goes they should stay away.",
    "importance": "medium",
    "ledger": [
     12
    ]
   }
  ]
 },
 {
  "id": "scene_3",
  "location": "The Clumsy Fox Tavern",
  "people": {
   "party": [
    "Sir Phidipaldi",
    "Wayman Tisdale",
    "Dr. Uriah"
   ],
   "others": [
    "Bentley",
    "Lady Hilda",
    "Eric the Reeve",
    "Drop Dead Ned"
   ]
  },
  "cue": "Sir Phidipaldi slapping the Reeve with his glove",
  "beats": [
   {
    "id": "beat_7",
    "kind": "event",
    "text": "On Sir Phidipaldi's recommendation that the busy inn would be higher status and full of rumors, he, Wayman and Dr. Uriah went into the Clumsy Fox.",
    "importance": "low",
    "ledger": [
     14,
     17
    ]
   },
   {
    "id": "beat_8",
    "kind": "event",
    "text": "Sir Phidipaldi told the red-headed noblewoman Lady Hilda she looked as fine as his oversized lance, Lady Isaboob; unflappable, she bought him a drink and he told her the party was on a chivalric quest for treasure.",
    "importance": "low",
    "ledger": [
     18,
     19,
     20,
     21,
     22,
     23,
     24
    ]
   },
   {
    "id": "beat_9",
    "kind": "event",
    "text": "Lady Hilda, a seasoned fighter in chain mail with a shield, mentioned rumors of a dragon and pointed out Eric the Reeve as trying to hire someone to kill it; she would not do it alone but offered to join a party of adventurers for money, and Sir Phidipaldi said they would talk to the Reeve and come back for her services.",
    "importance": "medium",
    "ledger": [
     25,
     27,
     28
    ]
   },
   {
    "id": "beat_10",
    "kind": "event",
    "text": "Dr. Uriah sensed no curses in the tavern but noticed a greasy-haired thief wearing a small jar on a necklace with a wasp buzzing inside.",
    "importance": "low",
    "ledger": [
     29,
     30
    ]
   },
   {
    "id": "beat_11",
    "kind": "event",
    "text": "Bentley, the halfling owner, gave Wayman a free Fox Tail Brew, which tasted fantastic, and offered rooms at 10 silver a night.",
    "importance": "low",
    "ledger": [
     31,
     32,
     33,
     34
    ]
   },
   {
    "id": "beat_12",
    "kind": "learned",
    "text": "Bentley says the town is downhearted over the rumored nearby dragon, and his shipment to restock the tavern was due a week ago and never arrived, hurting the whole town. Nothing like this has happened since Sir Brandon killed the first dragon hundreds of years ago. The townsfolk can't afford adventurers, but the Reeve has been trying to get help. Wayman asked whether anyone had gone after the missing shipment.",
    "importance": "medium",
    "ledger": [
     35,
     36
    ]
   },
   {
    "id": "beat_13",
    "kind": "event",
    "text": "Sir Phidipaldi introduced himself to the visibly stressed Eric the Reeve, showing off Lady Isaboob and his two-handed sword Sir Chumunga, which he can barely lift.",
    "importance": "low",
    "ledger": [
     51,
     52,
     53,
     54,
     55
    ]
   },
   {
    "id": "beat_14",
    "kind": "event",
    "text": "Eric the Reeve offered 1000 gold to whoever kills the dragon and drags its body into town, saying it was the first of many problems he has.",
    "importance": "high",
    "ledger": [
     56
    ]
   },
   {
    "id": "beat_15",
    "kind": "learned",
    "text": "Eric says George, a capable woodsman who lives a couple of houses down and might show up at the tavern tonight, encountered the dragon and lost an arm when it ripped it off; George described it as a black dragon, not a big one, and does not know where his arm is.",
    "importance": "medium",
    "ledger": [
     58,
     65
    ]
   },
   {
    "id": "beat_16",
    "kind": "event",
    "text": "Sir Phidipaldi told Eric that black dragons don't exist and that verified sightings were illusions by Clurichens, which he claimed steal limbs; Dr. Uriah knew this was wrong, and so did Eric.",
    "importance": "medium",
    "ledger": [
     59,
     60,
     61,
     62,
     63
    ]
   },
   {
    "id": "beat_17",
    "kind": "event",
    "text": "When the offended Eric defended George's account, Sir Phidipaldi slapped him with his glove and challenged him to a duel at dawn; the flustered Eric only said Sir Phidipaldi was more skilled at adventure, without accepting.",
    "importance": "high",
    "ledger": [
     64,
     65,
     66,
     67,
     68,
     69
    ]
   },
   {
    "id": "beat_18",
    "kind": "event",
    "text": "Dr. Uriah brought the thief a Fox Tail Brew; the man recognized him as a Dagonite and introduced himself as Drop Dead Ned, and Uriah said he was a scholar of folk remedies and lore looking for work with his crew.",
    "importance": "low",
    "ledger": [
     71,
     72,
     73,
     74
    ]
   },
   {
    "id": "beat_19",
    "kind": "event",
    "text": "Drop Dead Ned offered himself and his killer wasp for hire at 100 gold for the week, doing anything as long as he gets to kill people with the wasp; when Uriah asked for future reference about a night of at least ten kills, Ned kept the fee but offered back 5 gold per kill if he could do what he wanted with the victims, and Uriah said he would think about it.",
    "importance": "medium",
    "ledger": [
     75,
     78,
     79,
     80
    ]
   },
   {
    "id": "beat_20",
    "kind": "learned",
    "text": "Ned says his wasp is for things he wants to kill fast, but he likes to kill slowly and watch them die. Dr. Uriah sensed nothing unusual about the jar.",
    "importance": "low",
    "ledger": [
     76,
     77
    ]
   },
   {
    "id": "beat_21",
    "kind": "event",
    "text": "As Sir Phidipaldi's argument with Eric grew heated, Bentley stepped in, forbade fighting in his tavern, and made Sir Phidipaldi stay the night at the Golden Egg while letting his friends stay, putting his drink on the house.",
    "importance": "medium",
    "ledger": [
     87,
     88,
     89
    ]
   }
  ]
 },
 {
  "id": "scene_4",
  "location": "Farmer Gill's farm",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Farmer Gill"
   ]
  },
  "cue": "Shamus, the shabby prize mule for 100 gold",
  "beats": [
   {
    "id": "beat_22",
    "kind": "event",
    "text": "Preferring solitude to the inns, Dunk split from the party to scavenge at the farm on the edge of town and met Farmer Gill on his porch.",
    "importance": "low",
    "ledger": [
     15,
     16,
     37,
     38,
     39
    ]
   },
   {
    "id": "beat_23",
    "kind": "event",
    "text": "Farmer Gill offered his shabby mule Shamus, his 'prize mule,' for 100 gold so Dunk could start a farm; Dunk asked whether he could trade work for it, and Gill said the big work needed was killing the dragon outside town.",
    "importance": "medium",
    "ledger": [
     40,
     41,
     42,
     43,
     44
    ]
   },
   {
    "id": "beat_24",
    "kind": "learned",
    "text": "Gill says long ago Sir Brandon met a fairy in the woods who gave him a magic sword; he and his friends killed a dragon that had terrorized the town for weeks, and the town was named after him. They were knighted, then all left, and Brandon died. That dragon was definitely dead, dragged through town and ripped apart hundreds of years ago; Gill assumes the current one is a different dragon and does not know where dragons come from.",
    "importance": "medium",
    "ledger": [
     44,
     45,
     46
    ]
   },
   {
    "id": "beat_25",
    "kind": "learned",
    "text": "Gill saw the current dragon, which saw him and wanted nothing to do with him; he sent his three sons after it and says they are trying to kill it now.",
    "importance": "medium",
    "ledger": [
     44
    ]
   },
   {
    "id": "beat_26",
    "kind": "event",
    "text": "Dunk asked to sleep in the barn and think over the offer; Gill welcomed him, and they got drunk on the porch on drinks from Gill's still while Gill shared gossip.",
    "importance": "low",
    "ledger": [
     48,
     49,
     81,
     82,
     86
    ]
   },
   {
    "id": "beat_27",
    "kind": "learned",
    "text": "Gill says Warwick the smith has little for sale since nothing has come into town in months, keeps adding lucky charms to his shop daily, and is growing more paranoid. He displays a beautiful mithril chain shirt, perhaps the best in the world, which he always refuses to sell; it would fit a normal-sized person but not Dunk.",
    "importance": "medium",
    "ledger": [
     82
    ]
   },
   {
    "id": "beat_28",
    "kind": "learned",
    "text": "Gill says Warwick has covered a wall of his shop with clovers, and guesses the charms may be to keep away Ingrid, the potion seller, who is hot for Warwick; Ingrid is where to go for potions.",
    "importance": "low",
    "ledger": [
     83,
     84
    ]
   }
  ]
 },
 {
  "id": "scene_5",
  "location": "The Golden Egg Tavern",
  "people": {
   "party": [
    "Sir Phidipaldi"
   ],
   "others": [
    "Bentley",
    "Quinn"
   ]
  },
  "cue": "Sir Phidipaldi clanking out, foretelling doom for the Clumsy Fox",
  "beats": [
   {
    "id": "beat_29",
    "kind": "event",
    "text": "Bentley escorted Sir Phidipaldi to the Golden Egg as he clanked along in plate mail with his lance and sword, blustering that Zeus's law of courtesy was no longer honored and that this foretold doom for the Clumsy Fox.",
    "importance": "low",
    "ledger": [
     90
    ]
   },
   {
    "id": "beat_30",
    "kind": "event",
    "text": "Quinn, the owner and only person in the empty Golden Egg, charged Sir Phidipaldi 10 silver for ale three times the price across the street and completely watered down.",
    "importance": "low",
    "ledger": [
     91,
     92,
     93,
     94,
     95,
     96,
     97
    ]
   },
   {
    "id": "beat_31",
    "kind": "learned",
    "text": "Quinn says however much good stock he buys, it is gone the next morning, with half the glasses empty or knocked over, so he waters down what little he has. He believes Bentley steals his good ale at night, reasoning that Bentley's Fox Tail Brew is so popular.",
    "importance": "medium",
    "ledger": [
     98,
     100
    ]
   },
   {
    "id": "beat_32",
    "kind": "event",
    "text": "Sir Phidipaldi offered to help Quinn get back at Bentley; Quinn offered 100 gold for the help and proposed staging a fake shipment to see what happens, and Sir Phidipaldi agreed that Quinn would bring bottles, they would fill them with water, and he would make a big show of delivering ale.",
    "importance": "high",
    "ledger": [
     99,
     101,
     102,
     103
    ]
   }
  ]
 }
]
</scenes>