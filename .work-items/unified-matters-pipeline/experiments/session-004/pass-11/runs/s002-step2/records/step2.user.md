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
  "name": "The unrecognized treasure map",
  "parent": null,
  "facts": [
   {
    "id": "fact_1",
    "kind": "want",
    "text": "Find the treasure the party is seeking."
   },
   {
    "id": "fact_2",
    "kind": "could_use",
    "text": "The party holds a treasure map marking several locations they don't recognize; they assume the treasure is probably at one of them."
   },
   {
    "id": "fact_3",
    "kind": "unknown",
    "text": "Where does the treasure lie?"
   }
  ]
 },
 {
  "id": "thread_2",
  "name": "The Clurichen from the riverbanks",
  "parent": null,
  "facts": [
   {
    "id": "fact_4",
    "kind": "threat",
    "text": "Reginald the frog says a little trickster creature called a Clurichen comes from the riverbanks into town every night, up to no good, and that the party should stay away wherever it goes."
   },
   {
    "id": "fact_5",
    "kind": "unknown",
    "text": "What does the Clurichen do when it comes into town at night?"
   }
  ]
 },
 {
  "id": "thread_3",
  "name": "The dragon and the Reeve's bounty",
  "parent": null,
  "facts": [
   {
    "id": "fact_6",
    "kind": "want",
    "text": "Kill the black dragon near Brandonsford and drag its body into town to collect Eric the Reeve's 1000 gold bounty."
   },
   {
    "id": "fact_7",
    "kind": "could_use",
    "text": "Lady Hilda would join the party's dragon hunt for pay."
   },
   {
    "id": "fact_8",
    "kind": "could_use",
    "text": "The woodsman George, who lives a couple of houses from the Clumsy Fox, encountered the black dragon and lost an arm to it; the party could ask him where he met it."
   },
   {
    "id": "fact_9",
    "kind": "unknown",
    "text": "Where is the black dragon, and where did it come from?"
   },
   {
    "id": "fact_10",
    "kind": "threat",
    "text": "The black dragon outside Brandonsford, which tore off the woodsman George's arm, may maim others who encounter it."
   }
  ]
 },
 {
  "id": "thread_4",
  "name": "Lady Hilda's offer to join the dragon hunt",
  "parent": "thread_3",
  "facts": [
   {
    "id": "fact_11",
    "kind": "could_use",
    "text": "Lady Hilda, a seasoned fighter who says she can't hunt the dragon alone, offers to join the party for money to hunt it."
   },
   {
    "id": "fact_12",
    "kind": "owe",
    "text": "Sir Phidipaldi told Lady Hilda the party would talk with the Reeve and come back to take up her services."
   }
  ]
 },
 {
  "id": "thread_5",
  "name": "Drop Dead Ned's offer of hire",
  "parent": null,
  "facts": [
   {
    "id": "fact_13",
    "kind": "could_use",
    "text": "Drop Dead Ned offers himself and his killer wasp for hire at 100 gold a week, doing anything as long as he gets to kill; he will refund 5 gold per kill he is allowed if he can do what he wants with the bodies."
   }
  ]
 },
 {
  "id": "thread_6",
  "name": "Brandonsford's missing shipments",
  "parent": null,
  "facts": [
   {
    "id": "fact_14",
    "kind": "unknown",
    "text": "Why has nothing, including Bentley's restock shipment, come into Brandonsford for months?"
   }
  ]
 },
 {
  "id": "thread_7",
  "name": "Sir Phidipaldi's quarrel with Eric the Reeve",
  "parent": null,
  "facts": [
   {
    "id": "fact_15",
    "kind": "want",
    "text": "Sir Phidipaldi wants to fight Eric the Reeve in a duel at dawn."
   },
   {
    "id": "fact_16",
    "kind": "blocked_by",
    "text": "Eric the Reeve, offended by Sir Phidipaldi's false claims about George's dragon and the glove slap, did not accept the dawn duel, saying only that Sir Phidipaldi is more skilled at adventure."
   }
  ]
 },
 {
  "id": "thread_8",
  "name": "Buying Shamus the mule",
  "parent": null,
  "facts": [
   {
    "id": "fact_17",
    "kind": "want",
    "text": "Buy Shamus the mule from Farmer Gill, who asks 100 gold."
   },
   {
    "id": "fact_18",
    "kind": "could_use",
    "text": "Farmer Gill would accept killing the dragon outside town as work in trade for Shamus instead of 100 gold."
   }
  ]
 },
 {
  "id": "thread_9",
  "name": "Quinn's vanishing ale and the fake shipment",
  "parent": null,
  "facts": [
   {
    "id": "fact_19",
    "kind": "want",
    "text": "Help Quinn get back at Bentley, whom Quinn blames for stealing his ale at night, and collect Quinn's 100 gold."
   },
   {
    "id": "fact_20",
    "kind": "could_use",
    "text": "Sir Phidipaldi and Quinn agreed to stage a fake ale shipment: Quinn brings bottles to fill with water and Sir Phidipaldi makes a big show of delivering them."
   },
   {
    "id": "fact_21",
    "kind": "unknown",
    "text": "Who or what empties Quinn's good stock at the Golden Egg every night?"
   }
  ]
 }
]
</prior_threads>

<starting_situation>
Current position: Sir Phidipaldi is at the Golden Egg Tavern with its owner Quinn. Wayman and Dr. Uriah are across the street at the Clumsy Fox Tavern. Dunk is at Farmer Gill's farm on the edge of town, where Gill has welcomed him to sleep in the barn.
Immediate intention: Sir Phidipaldi and Quinn are setting up a fake ale shipment to catch Bentley. Quinn is to bring bottles to fill with water, and Sir Phidipaldi will make a big show of delivering them.
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
    "text": "At sunset Dunk and Farmer Gill drank steadily together, Dunk holding his drink far better, and Gill offered Dunk a free bed in his barn for the night.",
    "importance": "low"
   },
   {
    "id": "beat_2",
    "kind": "event",
    "text": "Dunk said he might take the bed but first offered 20 gold for Seamus the mule. Gill said he would go lower, but he could not work without his boys or a mule, and would drop the price once his boys came back.",
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
    "id": "beat_3",
    "kind": "event",
    "text": "Dr. Uriah, who carries the party's map, tried to recall its history but knew nothing about it, and planned to secretly copy it during his downtime.",
    "importance": "medium"
   },
   {
    "id": "beat_4",
    "kind": "event",
    "text": "Having been thrown out of the Clumsy Fox, Sir Phidipaldi could only sleep at the Golden Egg, which is empty and has no regulars, while Trout and Dr. Uriah lodged at the Clumsy Fox for 10 silver a night.",
    "importance": "low"
   },
   {
    "id": "beat_5",
    "kind": "event",
    "text": "Trout listened in unnoticed on the adventurers' table: Lady Hilda, Drop Dead Ned with his wasp necklace, the boisterous, joking human wizard Malzatarik the Magnificent, and a halfling sitting alone.",
    "importance": "low"
   },
   {
    "id": "beat_6",
    "kind": "event",
    "text": "Trout chummed up to the lone halfling, Squints, who said he had just come to town looking for his big break and wanted an adventuring crew to join, and showed off his sling.",
    "importance": "medium"
   },
   {
    "id": "beat_7",
    "kind": "event",
    "text": "Trout invited Squints to meet him there the next morning to be introduced to his friends and called it too early to discuss pay. Squints agreed.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_3",
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
    "id": "beat_8",
    "kind": "event",
    "text": "Sir Phidipaldi slept in the Golden Egg's basement, where Quinn keeps his alcohol, hoping to find a secret door, since Quinn would pay him for finding who was taking the booze.",
    "importance": "medium"
   },
   {
    "id": "beat_9",
    "kind": "event",
    "text": "Sir Phidipaldi covered the basement floor with his bag of marbles in anticipation of the thief.",
    "importance": "low"
   },
   {
    "id": "beat_10",
    "kind": "event",
    "text": "The basement door flung open on its own, and the invisible Clurichen slipped on the marbles, landed on its back and turned visible. When it said it was a good luck spirit, Sir Phidipaldi offered it a game of cards.",
    "importance": "medium"
   },
   {
    "id": "beat_11",
    "kind": "event",
    "text": "Trout and Dr. Uriah kicked the basement door open. Uriah threw vials of ink to reveal anything invisible, and Trout leapt in and caught the ink-soaked Clurichen in his bag of fish.",
    "importance": "medium"
   },
   {
    "id": "beat_12",
    "kind": "event",
    "text": "The Clurichen, Naggeneen, begged to be let go, offering his pot of gold or a secret. Sir Phidipaldi refused out of honor, having already called Quinn down.",
    "importance": "medium"
   },
   {
    "id": "beat_13",
    "kind": "learned",
    "text": "The thief of Quinn's alcohol was Naggeneen the Clurichen, not Bentley as Quinn had suspected. Naggeneen says he just likes to drink, has a problem, and drinks to unwind at night.",
    "importance": "high"
   },
   {
    "id": "beat_14",
    "kind": "event",
    "text": "Quinn said he knew what he would do with this one, hung the flailing bag on a hook behind his bar, and paid Sir Phidipaldi, Trout and Dr. Uriah 33 gold each.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_4",
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
    "id": "beat_15",
    "kind": "event",
    "text": "Dunk stayed up and went to look around Warwick the smith's closed shop. It doubles as his home, sits about a fifth of a mile from Gill's farm, and is covered in horseshoes, rabbit feet and clovers.",
    "importance": "low"
   },
   {
    "id": "beat_16",
    "kind": "event",
    "text": "Peeking through the window, Dunk saw iron daggers, a long sword, junk, and a mithril chain shirt glowing in the moonlight, clearly magical. Warwick was snoring in a second-story bedroom with its window cracked open.",
    "importance": "high"
   },
   {
    "id": "beat_17",
    "kind": "event",
    "text": "A thin, frazzled woman heading for the house saw Dunk, stiffened, and diverted as if she had not been going there. Dunk followed her.",
    "importance": "medium"
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
    "the Clurichen"
   ]
  },
  "beats": [
   {
    "id": "beat_18",
    "kind": "event",
    "text": "Dr. Uriah planned to nap until his ability to speak to animals returned, then stake out the river and follow the Clurichen when it emerged.",
    "importance": "low"
   },
   {
    "id": "beat_19",
    "kind": "learned",
    "text": "Talking to the Clurichen does not require the ability to talk to aquatic animals.",
    "importance": "low"
   },
   {
    "id": "beat_20",
    "kind": "event",
    "text": "Trout spear-fished at the river just outside town and caught several fish unseen. He saw Dr. Uriah arrive and hide, though Uriah did not notice him.",
    "importance": "low"
   },
   {
    "id": "beat_21",
    "kind": "learned",
    "text": "The Clurichen swims across the river towing a corked jug, drags it up the bank and turns invisible, but its little footprints show in the reeds.",
    "importance": "medium"
   },
   {
    "id": "beat_22",
    "kind": "event",
    "text": "Dr. Uriah followed the footprints unseen, with Trout behind him, to the Golden Egg Tavern's basement door.",
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
    "id": "beat_23",
    "kind": "event",
    "text": "Dunk followed the woman to Ingrid the Alchemist's shop and adjoining home, where she pretended to do chores, and he introduced himself.",
    "importance": "low"
   },
   {
    "id": "beat_24",
    "kind": "learned",
    "text": "Ingrid says she sells mandrake root tea that heals all wounds, witch powder that glows when sprinkled on anything magical, and essence of wolfsbane against wolves.",
    "importance": "medium"
   },
   {
    "id": "beat_25",
    "kind": "event",
    "text": "When Ingrid asked whether Warwick had mentioned her, Dunk falsely said Warwick had mentioned a beautiful apothecary.",
    "importance": "low"
   },
   {
    "id": "beat_26",
    "kind": "learned",
    "text": "Ingrid loves Warwick but is too scared to talk to him and has never spoken to him. Every night she climbs up to leave little gifts on his windowsill and watches him sleep. Her biggest fear is that he wakes and learns she has been watching him through his window; she would die of shame.",
    "importance": "high"
   },
   {
    "id": "beat_27",
    "kind": "event",
    "text": "Ingrid asked Dunk, being tall, to put her gifts up for her. Dunk instead proposed that she make a potion to calm her nerves and he lift her into the house, so she could unlock Warwick's front door for him from inside. When she asked why he wanted in, he claimed to love clovers, and she grew dubious and would not go along.",
    "importance": "medium"
   },
   {
    "id": "beat_28",
    "kind": "event",
    "text": "Dunk then proposed that Ingrid make a sleeping potion, which he would help her get inside and give to Warwick, so she could watch him all night without fear of him waking.",
    "importance": "medium"
   },
   {
    "id": "beat_29",
    "kind": "learned",
    "text": "Ingrid says she knows how to make such a potion but needs a key ingredient, among others: wine from the Fauns Grove, in the woods slightly north of town across the river. The grove's trees bleed red wine instead of sap, the fauns collect it, and it can put any creature to sleep or make it drunk. The grove is close enough to reach the next day.",
    "importance": "high"
   },
   {
    "id": "beat_30",
    "kind": "event",
    "text": "Dunk said he would see what he could do and set a meeting with Ingrid at the same spot and time the next night.",
    "importance": "high"
   },
   {
    "id": "beat_31",
    "kind": "event",
    "text": "Ingrid thanked Dunk for keeping her romance secret and said she owed him. Dunk replied that he hadn't kept it secret yet, which left her looking a little scared.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_7",
  "location": "The Clumsy Fox Tavern",
  "people": {
   "party": [
    "Trout"
   ],
   "others": [
    "Squints"
   ]
  },
  "beats": [
   {
    "id": "beat_32",
    "kind": "event",
    "text": "The next morning Brandonsford bustled, though shipments still had not come in, and Naggeneen's bag still hung behind Quinn's bar at the Golden Egg.",
    "importance": "medium"
   },
   {
    "id": "beat_33",
    "kind": "event",
    "text": "At the Clumsy Fox, the halfling owner and his wife gratefully took Trout's fish. Lady Hilda, Malzatarik the Magnificent, Drop Dead Ned, Squints and Eric the Reeve were all there.",
    "importance": "low"
   },
   {
    "id": "beat_34",
    "kind": "event",
    "text": "Squints asked where the promised friends were. Trout put him off until later, leaving him waiting and disappointed.",
    "importance": "low"
   },
   {
    "id": "beat_35",
    "kind": "event",
    "text": "Trout offered Squints a junior assistant place in the party's Halfling Corps, which Trout leads. Squints would fund himself until the first treasure, then pick second after the elite members, get his own gear, fight monsters starting immediately, and take orders directly from Trout. Squints, starry-eyed, agreed to join.",
    "importance": "high"
   },
   {
    "id": "beat_36",
    "kind": "event",
    "text": "Squints, armed with a sling and a dagger, is a more experienced fighter than Trout.",
    "importance": "medium"
   },
   {
    "id": "beat_37",
    "kind": "event",
    "text": "Trout told Squints to follow him, observe, not talk too much, and ask for no more than three tips a day. Squints agreed.",
    "importance": "low"
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
    "id": "beat_38",
    "kind": "event",
    "text": "Dr. Uriah visited the church, the only fully stone building in town. Father William, prejudiced against nonhumans, remarked pointedly on Uriah being a Dagonite and dismissed him as an amateur scholar come to profit from rumors of the dragon.",
    "importance": "medium"
   },
   {
    "id": "beat_39",
    "kind": "event",
    "text": "Dr. Uriah said he had not known about the dragon before arriving, but admitted he had been offered money to go after it.",
    "importance": "low"
   },
   {
    "id": "beat_40",
    "kind": "learned",
    "text": "Father William says he sent Brother Dirk a while ago to kill the dragon. Dirk had to go to Brandon's Barrow Mound first, because the dragon cannot be killed without the magic sword buried with Brandon.",
    "importance": "high"
   },
   {
    "id": "beat_41",
    "kind": "learned",
    "text": "The Barrow Mound is about a day's walk from town.",
    "importance": "medium"
   },
   {
    "id": "beat_42",
    "kind": "event",
    "text": "Doubting that Dagonites walk, Father William measured Dr. Uriah's hand and later his feet with a little pocket ruler, wrote the results down, and conceded there was no webbing.",
    "importance": "low"
   },
   {
    "id": "beat_43",
    "kind": "learned",
    "text": "Father William has no books for Dr. Uriah but offers to heal him if he is injured.",
    "importance": "medium"
   },
   {
    "id": "beat_44",
    "kind": "learned",
    "text": "Father William says Ingrid keeps scrolls, that she and the witch in the woods have a coven, and that Ingrid is incompetent and cannot make her potions herself.",
    "importance": "medium"
   },
   {
    "id": "beat_45",
    "kind": "event",
    "text": "Dr. Uriah agreed to Father William's requests to give penance at the Barrow Mound and donate 10 gold for its upkeep. Father William then marked the witch's home and the Barrow Mound on the party's map.",
    "importance": "high"
   },
   {
    "id": "beat_46",
    "kind": "event",
    "text": "Dr. Uriah searched the church for secret doors and found none.",
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
    "id": "beat_47",
    "kind": "event",
    "text": "Sir Phidipaldi visited one-armed George the Hunter at his woodsman's hut and asked about the Black Dragon.",
    "importance": "low"
   },
   {
    "id": "beat_48",
    "kind": "learned",
    "text": "George says the dragon's lair is up north at the foot of the mountains, reachable without climbing. It cannot fly yet but soon will, and then the town is doomed.",
    "importance": "high"
   },
   {
    "id": "beat_49",
    "kind": "learned",
    "text": "George says he went to the lair to kill the dragon and it killed all his friends. Its jaws drip poison and one bite kills, which is why he chopped off his own arm. It spits sulfur that smells of rotten eggs, and nothing pierces its black scales; their arrows and swords all failed.",
    "importance": "high"
   },
   {
    "id": "beat_50",
    "kind": "learned",
    "text": "George asked whether Eric had promised Sir Phidipaldi 1000 gold and said he doubts Eric has 1000 gold. Both men dislike Eric, though George says Eric thinks George is amazing.",
    "importance": "medium"
   },
   {
    "id": "beat_51",
    "kind": "learned",
    "text": "George says only Sir Brandon ever killed the dragon, 1000 or maybe 2000 years ago. Schoolchildren are taught that a little fairy gave Brandon a magic sword with which he killed it, but no one knows what is true or where the sword is. He says Farmer Gill knows the fairytales.",
    "importance": "medium"
   },
   {
    "id": "beat_52",
    "kind": "event",
    "text": "George said Sir Phidipaldi could repay him by killing the dragon but doubted he could, though he allowed that a lance might be one of the few weapons they never tried. Sir Phidipaldi vowed to bring his lance.",
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
    "the fauns"
   ]
  },
  "beats": [
   {
    "id": "beat_53",
    "kind": "event",
    "text": "Dunk set out alone from Gill's farmhouse to the Faun Grove, where he found fauns dancing to mandolin music and drinking from golden goblets, each wearing a necklace with a little flask.",
    "importance": "low"
   },
   {
    "id": "beat_54",
    "kind": "event",
    "text": "Dunk joined the dancing and drank both the fauns' wine and their emergency flask wine without effect, leaving the fauns gobsmacked.",
    "importance": "medium"
   },
   {
    "id": "beat_55",
    "kind": "learned",
    "text": "The fauns say almost any creature except fauns gets drunk immediately from a sip of their wine. The emergency wine in their neck flasks is the same wine, collected from trees that bleed red and white.",
    "importance": "medium"
   },
   {
    "id": "beat_56",
    "kind": "learned",
    "text": "The fauns collect little sentimental items and will trade for things like a love letter or a pixie's treasure.",
    "importance": "medium"
   },
   {
    "id": "beat_57",
    "kind": "event",
    "text": "Asking for wine to carry for anxious times, Dunk traded a crusty rabbit's foot from a child in his village for a faun's necklace flask of faun wine.",
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
    "id": "beat_58",
    "kind": "event",
    "text": "Dr. Uriah and Ingrid agreed that Father William was the worst, and Uriah passed on William's claim that she does not make her own potions.",
    "importance": "low"
   },
   {
    "id": "beat_59",
    "kind": "learned",
    "text": "Ingrid follows the religion of the forest, which she says the church represses. She says things have changed: there is the dragon, and fairies that used to stay hidden are encroaching and coming out more often. She sees them on visits to her friend Vivian, who lives in the forest.",
    "importance": "medium"
   },
   {
    "id": "beat_60",
    "kind": "learned",
    "text": "Asked whether Vivian is a witch, Ingrid says they are trying to reclaim the word; witches mostly do not marry and live solitary lives, perhaps with a friend such as an alchemist. She says she makes all her products herself, contradicting Father William.",
    "importance": "medium"
   },
   {
    "id": "beat_61",
    "kind": "learned",
    "text": "Ingrid's prices are 5 gold for wolfsbane, 7 gold for witch powder and 10 gold for mandrake tea.",
    "importance": "low"
   },
   {
    "id": "beat_62",
    "kind": "event",
    "text": "Dr. Uriah bought wolfsbane and mandrake root tea and passed on the witch powder.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_12",
  "location": "The Clumsy Fox Tavern",
  "people": {
   "party": [
    "Sir Phidipaldi",
    "Trout",
    "Dunk",
    "Dr. Uriah"
   ],
   "others": [
    "Squints"
   ]
  },
  "beats": [
   {
    "id": "beat_63",
    "kind": "event",
    "text": "Sir Phidipaldi returned to the Clumsy Fox and met Trout and Squints. Dunk arrived after more than 24 hours away, and Trout introduced Squints as having just joined up.",
    "importance": "low"
   },
   {
    "id": "beat_64",
    "kind": "event",
    "text": "Dunk told the others that Warwick the smith has beautiful armor that shimmers in the moonlight and could help against the dragon, and said he had a plan to get it and would go out one more night before rejoining them.",
    "importance": "high"
   },
   {
    "id": "beat_65",
    "kind": "event",
    "text": "Dunk bought a flask of wine for one gold.",
    "importance": "low"
   },
   {
    "id": "beat_66",
    "kind": "event",
    "text": "Sir Phidipaldi shared that the dragon is poisonous, spits sulfur and has unpierceable scales, and that the sword is at the Barrow. Dr. Uriah warned that the priest is a racist who won't like them.",
    "importance": "low"
   },
   {
    "id": "beat_67",
    "kind": "event",
    "text": "Trout pointed out that Brother Dirk was headed to the Barrow to fight the dragon, and Sir Phidipaldi added that Farmer Gill's sons were after the dragon too.",
    "importance": "medium"
   },
   {
    "id": "beat_68",
    "kind": "learned",
    "text": "The Barrow is roughly a three-mile walk through the forest, shorter than the day's walk given earlier.",
    "importance": "low"
   },
   {
    "id": "beat_69",
    "kind": "event",
    "text": "At Trout's proposal, the party decided to walk to the Barrow, avoiding the witch's house and checking out a marked map location on the way. Trout told Dunk to meet them there.",
    "importance": "high"
   }
  ]
 },
 {
  "id": "scene_13",
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
    "id": "beat_70",
    "kind": "event",
    "text": "Dunk heavily diluted the faun wine with tavern wine, about 20% faun wine to 80% tavern wine, so it still smelled like something Ingrid would recognize, and gave it to her.",
    "importance": "high"
   },
   {
    "id": "beat_71",
    "kind": "event",
    "text": "Ingrid said she would work on the potion and told Dunk to come back tomorrow. Dunk said he would see her tonight.",
    "importance": "medium"
   }
  ]
 },
 {
  "id": "scene_14",
  "location": "The giant's cottage",
  "people": {
   "party": [
    "Dunk",
    "Sir Phidipaldi",
    "Trout",
    "Dr. Uriah"
   ],
   "others": [
    "Squints",
    "the giant",
    "Brother Dirk"
   ]
  },
  "beats": [
   {
    "id": "beat_72",
    "kind": "event",
    "text": "The party, with Dunk and Squints, headed north through the woods and found a cottage three times normal size, built of cyclopean rocks, with a horrible roaring drone coming from inside.",
    "importance": "medium"
   },
   {
    "id": "beat_73",
    "kind": "event",
    "text": "Trout boosted Squints to the high window. Squints saw a wriggling, human-sized sack pinned to the wall beside the sleeping giant, with a pot cooking under the chimney.",
    "importance": "medium"
   },
   {
    "id": "beat_74",
    "kind": "event",
    "text": "Trout told Squints that intelligence suggested the sack held members of another adventuring party going after the dragon, and ordered him to bring it out unseen, promising to intervene if he was caught. Trout then whispered to the others that they would not actually rescue Squints, and Sir Phidipaldi agreed.",
    "importance": "medium"
   },
   {
    "id": "beat_75",
    "kind": "event",
    "text": "Dunk and Sir Phidipaldi waited at the door, Dr. Uriah at the other window, and Trout on the windowsill with his sling ready.",
    "importance": "low"
   },
   {
    "id": "beat_76",
    "kind": "event",
    "text": "Squints crept in, froze when the giant stirred, and pulled the sack down. A bound and gagged Brother Dirk fell out, and the giant woke demanding who was there.",
    "importance": "high"
   },
   {
    "id": "beat_77",
    "kind": "event",
    "text": "Dr. Uriah smashed the other window as a distraction, and Squints got Dirk out through the door that Dunk and Sir Phidipaldi opened.",
    "importance": "medium"
   },
   {
    "id": "beat_78",
    "kind": "event",
    "text": "Trout fired his sling at the giant's head but hit Squints in the head instead.",
    "importance": "low"
   },
   {
    "id": "beat_79",
    "kind": "event",
    "text": "The party fled across the field. The slow giant chased them for a while before tiring, and they easily outran him.",
    "importance": "medium"
   },
   {
    "id": "beat_80",
    "kind": "learned",
    "text": "Brother Dirk says the giant was going to eat him in its stew. He was captured on his way to the Barrow to get the sword and save the town.",
    "importance": "medium"
   },
   {
    "id": "beat_81",
    "kind": "event",
    "text": "Brother Dirk said he should just head home. Sir Phidipaldi said they were also headed to the Barrow and objected to Dirk leaving, and Dr. Uriah asked what Father William would say, since William believed sending Dirk had settled the dragon problem.",
    "importance": "high"
   },
   {
    "id": "beat_82",
    "kind": "event",
    "text": "Trout told Brother Dirk he would report to Squints, which pleased Squints, who reasoned that he had rescued Dirk.",
    "importance": "low"
   }
  ]
 }
]
</scenes>