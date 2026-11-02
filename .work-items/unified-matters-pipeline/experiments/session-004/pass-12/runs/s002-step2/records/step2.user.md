<session_attendees>
- Jason Beaumont: Game Master
- Marshall Riser: Dunk
- Erik Saltwell: Sir Phidipaldi
- Jeff DeVries: Trout
- Rich Gredzinski: Dr. Uriah
</session_attendees>

<prior_threads>
[
 {
  "id": "thread_1",
  "name": "The treasure map",
  "parent": null,
  "facts": [
   {
    "id": "fact_1",
    "kind": "want",
    "text": "Find the treasure marked on the party's treasure map."
   },
   {
    "id": "fact_2",
    "kind": "could_use",
    "text": "The party holds a treasure map marking several locations around Brandonsford that they don't recognize; they assume the treasure is at one of them."
   },
   {
    "id": "fact_3",
    "kind": "unknown",
    "text": "Where are the locations marked on the treasure map, and which one holds the treasure?"
   }
  ]
 },
 {
  "id": "thread_2",
  "name": "The Brandonsford dragon",
  "parent": null,
  "facts": [
   {
    "id": "fact_4",
    "kind": "want",
    "text": "Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000 gold."
   },
   {
    "id": "fact_5",
    "kind": "could_use",
    "text": "Eric the Reeve says the woodsman George, who met the dragon and lost an arm to it, lives a couple of houses down and may come to the Clumsy Fox tonight; the party could question him about where and how he encountered it."
   },
   {
    "id": "fact_6",
    "kind": "unknown",
    "text": "Where can the black dragon be found?"
   },
   {
    "id": "fact_7",
    "kind": "threat",
    "text": "The black dragon, which took woodsman George's arm, remains loose around Brandonsford and may maim those who confront it."
   },
   {
    "id": "fact_8",
    "kind": "unknown",
    "text": "What will become of Farmer Gill's three sons, who are out trying to kill the dragon now?"
   },
   {
    "id": "fact_9",
    "kind": "could_use",
    "text": "Lady Hilda's offer to join the hunt for pay (thread_4) could add a seasoned fighter against the dragon."
   }
  ]
 },
 {
  "id": "thread_3",
  "name": "The Clurichen",
  "parent": null,
  "facts": [
   {
    "id": "fact_10",
    "kind": "threat",
    "text": "Reginald the Frog warns that a little trickster creature called a Clurichen comes from the riverbanks into Brandonsford every night, up to no good, and that the party should stay away from wherever it goes."
   },
   {
    "id": "fact_11",
    "kind": "unknown",
    "text": "What does the Clurichen do when it comes into town each night?"
   }
  ]
 },
 {
  "id": "thread_4",
  "name": "Lady Hilda's offer to join the hunt",
  "parent": "thread_2",
  "facts": [
   {
    "id": "fact_12",
    "kind": "could_use",
    "text": "Lady Hilda, a seasoned fighter in chain mail and shield, would join the party for pay to hunt the dragon, which she can't hunt alone."
   },
   {
    "id": "fact_13",
    "kind": "owe",
    "text": "Sir Phidipaldi told Lady Hilda the party would talk to the Reeve and come back to hire her."
   }
  ]
 },
 {
  "id": "thread_5",
  "name": "Brandonsford's missing shipments",
  "parent": null,
  "facts": [
   {
    "id": "fact_14",
    "kind": "unknown",
    "text": "Why have shipments stopped reaching Brandonsford? Bentley's tavern restock is a week overdue, and Farmer Gill says nothing has come into town in months."
   }
  ]
 },
 {
  "id": "thread_6",
  "name": "Drop Dead Ned's offer",
  "parent": null,
  "facts": [
   {
    "id": "fact_15",
    "kind": "could_use",
    "text": "Drop Dead Ned, a murderous thief with a killer wasp in a jar, offers to hire on with the party for 100 gold a week, willing to do anything as long as he gets to kill people; Dr. Uriah said he'd think about it."
   }
  ]
 },
 {
  "id": "thread_7",
  "name": "Shamus the mule",
  "parent": null,
  "facts": [
   {
    "id": "fact_16",
    "kind": "want",
    "text": "Dunk wants Farmer Gill's mule Shamus, which Gill will sell for 100 gold."
   },
   {
    "id": "fact_17",
    "kind": "could_use",
    "text": "Farmer Gill would accept work in place of the 100 gold for Shamus, and says the big work he needs is killing the dragon."
   }
  ]
 },
 {
  "id": "thread_8",
  "name": "Quinn's fake shipment scheme",
  "parent": null,
  "facts": [
   {
    "id": "fact_18",
    "kind": "want",
    "text": "Catch whoever empties the Golden Egg's bar at night, which Quinn blames on Bentley, and collect Quinn's 100 gold."
   },
   {
    "id": "fact_19",
    "kind": "could_use",
    "text": "Sir Phidipaldi and Quinn agreed a plan: Quinn brings bottles, they fill them with water, and Sir Phidipaldi makes a big show of delivering ale to the Golden Egg to lure whoever empties the bar."
   },
   {
    "id": "fact_20",
    "kind": "unknown",
    "text": "Who or what empties and knocks over the Golden Egg's stock every night? Quinn blames Bentley."
   }
  ]
 }
]
</prior_threads>

<starting_situation>
Current position: Sir Phidipaldi is at the Golden Egg Tavern with its owner, Quinn. Wayman and Dr. Uriah are at the Clumsy Fox Tavern. Dunk is at Farmer Gill's farm on the edge of town, drinking with Gill on the porch.
Immediate intention: Sir Phidipaldi and Quinn are about to stage a fake ale shipment for Quinn's offer of 100 gold. Quinn will bring bottles, they will fill them with water, and Sir Phidipaldi will make a big show of delivering them to see what happens.
</starting_situation>

<scenes>
[
 {
  "id": "scene_1",
  "location": "Farmer Gill's farm",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Farmer Gill"
   ]
  },
  "beats": [
   {
    "id": "beat_1",
    "kind": "event",
    "text": "At sunset Dunk drank steadily with Farmer Gill on his porch, holding his drink far better than Gill.",
    "importance": "low"
   },
   {
    "id": "beat_2",
    "kind": "event",
    "text": "Farmer Gill offered Dunk a free bed in his barn for the night, and Dunk said he might take it.",
    "importance": "low"
   },
   {
    "id": "beat_3",
    "kind": "event",
    "text": "Dunk offered 20 gold for Gill's mule Seamus; Gill said he would go lower, but not until his boys come back, since without them or a mule he can't get any work done.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_2",
  "location": "The Clumsy Fox Tavern",
  "people": {
   "party": [
    "Trout",
    "Dr. Uriah"
   ],
   "others": [
    "Squints"
   ]
  },
  "beats": [
   {
    "id": "beat_4",
    "kind": "event",
    "text": "Dr. Uriah, who carries the party's map, could recall nothing of its history and planned to secretly copy it during his downtime.",
    "importance": "medium"
   },
   {
    "id": "beat_5",
    "kind": "event",
    "text": "Trout and Dr. Uriah took rooms at the Clumsy Fox at 10 silver a night; Sir Phidipaldi, having been thrown out of the Clumsy Fox, could only sleep at the nearly empty Golden Egg.",
    "importance": "low"
   },
   {
    "id": "beat_6",
    "kind": "event",
    "text": "Trout eavesdropped unnoticed on the adventurers' table: Lady Hilda, Drop Dead Ned with his wasp necklace, the boisterous human wizard Malzatarik the Magnificent, and a shifty halfling sitting alone.",
    "importance": "low"
   },
   {
    "id": "beat_7",
    "kind": "event",
    "text": "Trout befriended the lone halfling, Squints, a sling-user new to town looking for his big break with an adventuring crew; Trout said he was a river halfling from Bobbity Ba seeking profit and adventure.",
    "importance": "medium"
   },
   {
    "id": "beat_8",
    "kind": "event",
    "text": "Trout invited Squints to meet him at the Clumsy Fox the next morning to be introduced to his friends, putting off talk of pay, and Squints agreed.",
    "importance": "medium"
   },
   {
    "id": "beat_9",
    "kind": "event",
    "text": "Dr. Uriah planned to nap until his ability to speak with animals returned, then stake out the river to follow the Clurichen when it emerged.",
    "importance": "medium"
   },
   {
    "id": "beat_10",
    "kind": "learned",
    "text": "Talking with the Clurichen does not require the ability to speak with aquatic animals.",
    "importance": "low"
   }
  ]
 },
 {
  "id": "scene_3",
  "location": "Warwick's shop",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Ingrid"
   ]
  },
  "beats": [
   {
    "id": "beat_11",
    "kind": "event",
    "text": "Instead of sleeping, Dunk walked to Warwick the smith's closed shop, about a fifth of a mile down a dirt path from Gill's farm, and peeked in the window.",
    "importance": "low"
   },
   {
    "id": "beat_12",
    "kind": "learned",
    "text": "Warwick's shop doubles as his home and its exterior is covered in lucky charms: horseshoes, rabbit feet and nailed-up clovers.",
    "importance": "low"
   },
   {
    "id": "beat_13",
    "kind": "learned",
    "text": "Warwick's shop holds iron daggers, a long sword and much junk, plus a mithril chain shirt that glows in the moonlight and is clearly magical.",
    "importance": "high"
   },
   {
    "id": "beat_14",
    "kind": "learned",
    "text": "Warwick sleeps in a second-story bedroom whose window is left cracked open.",
    "importance": "medium"
   },
   {
    "id": "beat_15",
    "kind": "event",
    "text": "A thin, frazzled woman heading toward the house saw Dunk, stiffened and veered away as if she hadn't been going there.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_4",
  "location": "The Golden Egg Tavern's basement",
  "people": {
   "party": [
    "Sir Phidipaldi",
    "Trout",
    "Dr. Uriah"
   ],
   "others": [
    "Naggeneen",
    "Quinn"
   ]
  },
  "beats": [
   {
    "id": "beat_16",
    "kind": "event",
    "text": "Sir Phidipaldi slept in the Golden Egg's basement, where Quinn keeps his alcohol, hoping to find a secret door, since Quinn will pay him for finding who took the booze.",
    "importance": "medium"
   },
   {
    "id": "beat_17",
    "kind": "event",
    "text": "Sir Phidipaldi covered the basement floor with his bag of marbles to trap the thief.",
    "importance": "low"
   },
   {
    "id": "beat_18",
    "kind": "event",
    "text": "Dr. Uriah and Trout, separately, followed the invisible Clurichen's footprints to the Golden Egg, where the basement door flung open and shut with no one visible.",
    "importance": "low"
   },
   {
    "id": "beat_19",
    "kind": "event",
    "text": "The invisible Clurichen slipped on the marbles, landed on its back and turned visible; it claimed to be a good luck spirit, and Sir Phidipaldi offered it a game of cards.",
    "importance": "medium"
   },
   {
    "id": "beat_20",
    "kind": "event",
    "text": "Trout and Dr. Uriah kicked the door open, Uriah threw vials of ink to reveal anything invisible, and Trout captured the ink-soaked Clurichen in his bag of fish.",
    "importance": "high"
   },
   {
    "id": "beat_21",
    "kind": "learned",
    "text": "The Clurichen is named Naggeneen; he says he just likes to drink, has a problem, and drinks to unwind at night.",
    "importance": "medium"
   },
   {
    "id": "beat_22",
    "kind": "event",
    "text": "Naggeneen begged to be let go in exchange for his pot of gold or a secret; Sir Phidipaldi refused on grounds of honor and chivalry and called Quinn down.",
    "importance": "medium"
   },
   {
    "id": "beat_23",
    "kind": "learned",
    "text": "Quinn had suspected Bentley of stealing his alcohol; the thief caught was Naggeneen, who had a jug in the bag reeking of alcohol.",
    "importance": "medium"
   },
   {
    "id": "beat_24",
    "kind": "event",
    "text": "Naggeneen pleaded with Quinn and promised good luck if freed, but Quinn said he knew what he would do with him and hung the flailing bag on a hook behind the bar.",
    "importance": "medium"
   },
   {
    "id": "beat_25",
    "kind": "event",
    "text": "Quinn paid Sir Phidipaldi, Trout and Dr. Uriah 33 gold each as their reward for catching the thief.",
    "importance": "high"
   },
   {
    "id": "beat_26",
    "kind": "event",
    "text": "The next morning the bag holding Naggeneen still hung behind Quinn's bar.",
    "importance": "low"
   }
  ]
 },
 {
  "id": "scene_5",
  "location": "The river",
  "people": {
   "party": [
    "Trout",
    "Dr. Uriah"
   ],
   "others": [
    "Naggeneen"
   ]
  },
  "beats": [
   {
    "id": "beat_27",
    "kind": "event",
    "text": "Trout spear-fished in the river just outside town in the river-halfling way, catching several fish while staying all but unseen.",
    "importance": "low"
   },
   {
    "id": "beat_28",
    "kind": "event",
    "text": "Dr. Uriah came to the river and hid to wait for the Clurichen, without noticing Trout.",
    "importance": "low"
   },
   {
    "id": "beat_29",
    "kind": "event",
    "text": "The Clurichen swam across the river towing a corked jug, dragged it up the bank and turned invisible, leaving little footprints in the reeds.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_6",
  "location": "Ingrid's shop",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Ingrid"
   ]
  },
  "beats": [
   {
    "id": "beat_30",
    "kind": "event",
    "text": "Dunk followed the woman to the shop marked 'Ingrid the Alchemist' and her adjoining home, where she pretended to do chores, and he introduced himself.",
    "importance": "low"
   },
   {
    "id": "beat_31",
    "kind": "learned",
    "text": "Ingrid sells mandrake root tea that she says heals all wounds, witch powder that glows when sprinkled on anything magical, and essence of wolfsbane against wolves.",
    "importance": "medium"
   },
   {
    "id": "beat_32",
    "kind": "event",
    "text": "Asked about Warwick's, Ingrid blushed and deflected; Dunk falsely told her Warwick had mentioned a beautiful apothecary.",
    "importance": "low"
   },
   {
    "id": "beat_33",
    "kind": "learned",
    "text": "Ingrid secretly loves Warwick: she climbs up every night to leave gifts on his windowsill and watch him sleep, but has never spoken to him. Her biggest fear is that he will wake and learn she watches him nightly; she says she would die of shame.",
    "importance": "high"
   },
   {
    "id": "beat_34",
    "kind": "event",
    "text": "Ingrid asked the tall Dunk to put her gifts up for her; Dunk instead proposed lifting her into the house in exchange for her unlocking Warwick's front door for him, claiming he was a fan of clovers, and she grew dubious and did not agree.",
    "importance": "medium"
   },
   {
    "id": "beat_35",
    "kind": "event",
    "text": "Dunk proposed that Ingrid make a sleeping potion that he would help her administer to Warwick so she could watch him all night without fear of him waking.",
    "importance": "high"
   },
   {
    "id": "beat_36",
    "kind": "learned",
    "text": "Ingrid says she knows how to make the sleeping potion but needs a key ingredient: wine from the Fauns Grove, a short trip slightly north of town across the river, where the trees bleed red wine that the fauns collect and that can put any creature to sleep or make it drunk.",
    "importance": "high"
   },
   {
    "id": "beat_37",
    "kind": "event",
    "text": "Dunk said he would see what he could do and arranged to meet Ingrid at the same spot and time the next night.",
    "importance": "high"
   },
   {
    "id": "beat_38",
    "kind": "event",
    "text": "Ingrid thanked Dunk for keeping her romance secret and said she owes him; Dunk replied he hadn't kept it secret yet, and she looked scared.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_7",
  "location": "The Clumsy Fox Tavern",
  "people": {
   "party": [
    "Trout",
    "Sir Phidipaldi",
    "Dunk",
    "Dr. Uriah"
   ],
   "others": [
    "Squints",
    "The Clumsy Fox's halfling owner and his wife"
   ]
  },
  "beats": [
   {
    "id": "beat_39",
    "kind": "event",
    "text": "Next morning Brandonsford was bustling, though shipments still hadn't come in.",
    "importance": "low"
   },
   {
    "id": "beat_40",
    "kind": "event",
    "text": "The Clumsy Fox's halfling owner and his wife gratefully took Trout's fish; Lady Hilda, Malzatarik the Magnificent, Drop Dead Ned, Squints and Eric the Reeve were among the diners.",
    "importance": "low"
   },
   {
    "id": "beat_41",
    "kind": "event",
    "text": "Squints asked where the promised friends were, and Trout put him off until later, leaving him disappointed.",
    "importance": "low"
   },
   {
    "id": "beat_42",
    "kind": "event",
    "text": "Trout recruited Squints as a junior assistant in the party's Halfling Corps, led by Trout: Squints funds himself until the first treasure, then picks second after the elite members, gets his own gear, fights monsters starting immediately, and takes orders directly from Trout.",
    "importance": "high"
   },
   {
    "id": "beat_43",
    "kind": "event",
    "text": "Trout told Squints to follow, observe and not talk too much, allowing him three tips a day, and Squints agreed.",
    "importance": "low"
   },
   {
    "id": "beat_44",
    "kind": "learned",
    "text": "Squints is a more experienced fighter than Trout, armed with a sling and a dagger.",
    "importance": "medium"
   },
   {
    "id": "beat_45",
    "kind": "event",
    "text": "Sir Phidipaldi, then Dunk, returned to the Clumsy Fox and met Trout and Squints; Dunk had been away from his friends for over a day.",
    "importance": "low"
   },
   {
    "id": "beat_46",
    "kind": "event",
    "text": "Dunk told the others Warwick the smith has beautiful armor that shimmers in the moonlight and could help against the dragon, said he had a plan to get it, and said he would go out one more night before rejoining them.",
    "importance": "high"
   },
   {
    "id": "beat_47",
    "kind": "event",
    "text": "Dunk bought a flask of tavern wine for one gold; the Clumsy Fox sells wine at three silver a pint.",
    "importance": "low"
   },
   {
    "id": "beat_48",
    "kind": "event",
    "text": "Sir Phidipaldi shared George's account of the dragon's poison, sulfur spit and unpierceable scales, and that the sword is at the Barrow; Dr. Uriah warned that the priest is racist and won't like them.",
    "importance": "medium"
   },
   {
    "id": "beat_49",
    "kind": "event",
    "text": "Trout noted Brother Dirk was headed to the Barrow to fight the dragon, and Sir Phidipaldi added that Farmer Gill's sons are after the dragon too.",
    "importance": "medium"
   },
   {
    "id": "beat_50",
    "kind": "learned",
    "text": "The Barrow is roughly a three-mile walk through the forest, shorter than Father William's earlier estimate of about a day's walk.",
    "importance": "medium"
   },
   {
    "id": "beat_51",
    "kind": "event",
    "text": "At Trout's lead the party decided to walk to the Barrow to get the sword, avoiding the witch's house and checking out a marked location on the way, and told Dunk to meet them there.",
    "importance": "high"
   }
  ]
 },
 {
  "id": "scene_8",
  "location": "The church",
  "people": {
   "party": [
    "Dr. Uriah"
   ],
   "others": [
    "Father William"
   ]
  },
  "beats": [
   {
    "id": "beat_52",
    "kind": "event",
    "text": "Dr. Uriah visited the church, the only fully stone building in town, and met its gray-bearded priest Father William, who remarked pointedly on Uriah being a Dagonite.",
    "importance": "low"
   },
   {
    "id": "beat_53",
    "kind": "event",
    "text": "Uriah said he was a seeker of old knowledge and admitted he had been offered money to go after the dragon; Father William said they had nothing for amateur scholars.",
    "importance": "low"
   },
   {
    "id": "beat_54",
    "kind": "learned",
    "text": "Father William says he sent Brother Dirk a while ago to kill the dragon, and that Dirk first had to go to Brandon's Barrow Mound because the dragon can't be killed without the magic sword buried with Brandon.",
    "importance": "high"
   },
   {
    "id": "beat_55",
    "kind": "learned",
    "text": "The Barrow Mound is about a day's walk from town.",
    "importance": "low"
   },
   {
    "id": "beat_56",
    "kind": "event",
    "text": "Father William grabbed Uriah's hand and later his feet and measured them with a little ruler, conceding there was no webbing; Uriah told him he is not dangerous unless he wants to be.",
    "importance": "low"
   },
   {
    "id": "beat_57",
    "kind": "learned",
    "text": "Father William offers to heal Uriah if he is injured.",
    "importance": "medium"
   },
   {
    "id": "beat_58",
    "kind": "learned",
    "text": "Father William says Ingrid, 'that little pagan', keeps scrolls, has a coven with the witch in the woods, and is incompetent and can't make her potions herself.",
    "importance": "medium"
   },
   {
    "id": "beat_59",
    "kind": "event",
    "text": "At Father William's request, Uriah agreed to give penance at the Barrow Mound and to donate 10 gold for its upkeep; no payment was recorded.",
    "importance": "medium"
   },
   {
    "id": "beat_60",
    "kind": "event",
    "text": "Father William marked the witch's home and the Barrow Mound on Uriah's map.",
    "importance": "high"
   },
   {
    "id": "beat_61",
    "kind": "event",
    "text": "Uriah searched the church for secret doors and found none.",
    "importance": "low"
   }
  ]
 },
 {
  "id": "scene_9",
  "location": "George's hut",
  "people": {
   "party": [
    "Sir Phidipaldi"
   ],
   "others": [
    "George"
   ]
  },
  "beats": [
   {
    "id": "beat_62",
    "kind": "event",
    "text": "Sir Phidipaldi visited one-armed George the Hunter, busy tanning hides and chopping wood, to ask about the Black Dragon.",
    "importance": "low"
   },
   {
    "id": "beat_63",
    "kind": "learned",
    "text": "George says the dragon's lair is north at the foot of the mountains, reachable without climbing; it can't fly yet but will soon, and then he says they're doomed.",
    "importance": "high"
   },
   {
    "id": "beat_64",
    "kind": "learned",
    "text": "George says the dragon killed all his friends when they attacked its lair; its jaws drip poison and one bite kills, so he chopped off his own bitten arm; it spits sulfur smelling of rotten eggs; and arrows and swords could not pierce its black scales.",
    "importance": "high"
   },
   {
    "id": "beat_65",
    "kind": "learned",
    "text": "George doubts Eric the Reeve has the 1000 gold he promised for the dragon; Sir Phidipaldi called Eric a man of no honor, and George dislikes Eric too, though Eric admires him.",
    "importance": "medium"
   },
   {
    "id": "beat_66",
    "kind": "learned",
    "text": "George says only Sir Brandon ever killed the dragon, 1000 or 2000 years ago, with a magic sword schoolchildren are taught a little fairy gave him; no one knows what is true or where the sword is. Farmer Gill knows the fairytales.",
    "importance": "high"
   },
   {
    "id": "beat_67",
    "kind": "event",
    "text": "George allowed that a lance may be one of the few weapons not yet tried on the dragon, and Sir Phidipaldi vowed to bring his lance.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_10",
  "location": "The Faun Grove",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Fauns"
   ]
  },
  "beats": [
   {
    "id": "beat_68",
    "kind": "event",
    "text": "Dunk woke at Gill's farmhouse and went alone to the Faun Grove, where fauns wearing little neck flasks danced, played mandolins and drank from golden goblets.",
    "importance": "low"
   },
   {
    "id": "beat_69",
    "kind": "event",
    "text": "Dunk joined the dancing and drank the fauns' wine, then their emergency wine, with no effect, astonishing them.",
    "importance": "medium"
   },
   {
    "id": "beat_70",
    "kind": "learned",
    "text": "The fauns say almost any creature except fauns gets drunk immediately from their wine; their neck flasks hold 'emergency wine', the same wine collected from trees that bleed red and white.",
    "importance": "medium"
   },
   {
    "id": "beat_71",
    "kind": "learned",
    "text": "The fauns collect sentimental items and will trade for things like a love letter or a pixie's treasure.",
    "importance": "medium"
   },
   {
    "id": "beat_72",
    "kind": "event",
    "text": "Dunk traded a crusty rabbit's foot that had kept a child in his village safe for a faun's necklace flask of faun wine.",
    "importance": "high"
   }
  ]
 },
 {
  "id": "scene_11",
  "location": "Ingrid's shop",
  "people": {
   "party": [
    "Dr. Uriah"
   ],
   "others": [
    "Ingrid"
   ]
  },
  "beats": [
   {
    "id": "beat_73",
    "kind": "event",
    "text": "Dr. Uriah visited Ingrid's shop and bonded with her over disliking Father William.",
    "importance": "low"
   },
   {
    "id": "beat_74",
    "kind": "learned",
    "text": "Ingrid follows the religion of the forest and says the church represses the wood folk's secrets; she says fairies that used to stay hidden are encroaching more often, and she sees them when visiting her friend Vivian, who lives in the forest.",
    "importance": "medium"
   },
   {
    "id": "beat_75",
    "kind": "learned",
    "text": "Ingrid says she and Vivian are trying to reclaim the word 'witch', that witches mostly live solitary unmarried lives, and that she makes all her products herself, contradicting Father William's claim.",
    "importance": "medium"
   },
   {
    "id": "beat_76",
    "kind": "learned",
    "text": "Ingrid's prices: wolfsbane 5 gold, witch powder 7 gold, mandrake tea 10 gold.",
    "importance": "low"
   },
   {
    "id": "beat_77",
    "kind": "event",
    "text": "Dr. Uriah bought wolfsbane and mandrake tea, passing on the witch powder.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_12",
  "location": "Ingrid's shop",
  "people": {
   "party": [
    "Dunk"
   ],
   "others": [
    "Ingrid"
   ]
  },
  "beats": [
   {
    "id": "beat_78",
    "kind": "event",
    "text": "Dunk heavily diluted the faun wine, about 20% faun wine to 80% tavern wine, so Ingrid would still recognize the smell, and gave it to her.",
    "importance": "high"
   },
   {
    "id": "beat_79",
    "kind": "event",
    "text": "Ingrid said she would work on the potion and told Dunk to come back tomorrow; Dunk said he would see her tonight.",
    "importance": "high"
   }
  ]
 },
 {
  "id": "scene_13",
  "location": "The giant's cottage",
  "people": {
   "party": [
    "Trout",
    "Sir Phidipaldi",
    "Dunk",
    "Dr. Uriah"
   ],
   "others": [
    "Squints",
    "The giant",
    "Brother Dirk"
   ]
  },
  "beats": [
   {
    "id": "beat_80",
    "kind": "event",
    "text": "Dunk set out north through the woods with the party and Squints.",
    "importance": "low"
   },
   {
    "id": "beat_81",
    "kind": "event",
    "text": "In a clearing the party found a cottage three times normal size, built of huge rocks, with a roaring, droning sound from inside.",
    "importance": "low"
   },
   {
    "id": "beat_82",
    "kind": "event",
    "text": "Trout and Squints scouted, and Trout boosted Squints to the high window, from where he saw a sleeping giant, a pot cooking, and a wiggling human-sized sack pinned to the wall.",
    "importance": "medium"
   },
   {
    "id": "beat_83",
    "kind": "event",
    "text": "Trout told Squints this was his chance to prove himself, claiming intelligence that the sack held members of a rival dragon-hunting party, and promised to intervene if he was caught; Trout then whispered that they wouldn't actually rescue him, and Sir Phidipaldi agreed.",
    "importance": "medium"
   },
   {
    "id": "beat_84",
    "kind": "event",
    "text": "Squints crept in and pulled down the sack, and a bound and gagged Brother Dirk fell out as the giant woke.",
    "importance": "high"
   },
   {
    "id": "beat_85",
    "kind": "event",
    "text": "Dr. Uriah smashed a window to distract the giant while Dunk and Sir Phidipaldi held the door for Squints and Dirk to escape; Trout's sling shot at the giant hit Squints in the head instead.",
    "importance": "medium"
   },
   {
    "id": "beat_86",
    "kind": "event",
    "text": "The party fled across the field and easily outran the slow giant, who tired of the chase.",
    "importance": "medium"
   },
   {
    "id": "beat_87",
    "kind": "event",
    "text": "Dunk removed Brother Dirk's gag.",
    "importance": "low"
   },
   {
    "id": "beat_88",
    "kind": "learned",
    "text": "Brother Dirk says the giant captured him on his way to the Barrow to get the sword and save the town, and was going to eat him in a stew.",
    "importance": "medium"
   },
   {
    "id": "beat_89",
    "kind": "event",
    "text": "Brother Dirk said he thought he should just head home; Sir Phidipaldi objected, and Dr. Uriah asked what Father William would say, since William believed the dragon was handled by sending Dirk.",
    "importance": "high"
   },
   {
    "id": "beat_90",
    "kind": "event",
    "text": "Trout told Brother Dirk he would report to Squints, which pleased Squints; Dirk's response was not recorded.",
    "importance": "medium"
   }
  ]
 }
]
</scenes>