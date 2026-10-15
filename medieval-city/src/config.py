"""Personalise the city here, then run `python3 build.py` again.

Every name below flows into the blueprint sheets, the 3D model's object names
and the placement data, so renaming a place here renames it everywhere.
"""

SEED = 1331                     # change for different streets, houses, residents, trees and terrain noise

REALM = "Stonehallow"           # the city
REALM_TAGLINE = "A sprawling medieval port-city that grew without a plan"
YOU = "The Warden of the Stones"   # you: keeper of the city's ancient places
YOUR_HOUSE = "Wardenhouse"         # your home, beside the Kingstone

NAMES = {
    "river": "River Wend",
    "brook": "Hallow Brook",
    "sea": "The Grey Sea",
    "lake": "Mirror Mere",
    "island": "King's Isle",
    "sea_island": "Gull Rock",
    "headland": "Raven Head",
    "castle": "Crownhold",
    "keep": "The Crown Tower",
    "palace": "Palace of the Seven Gardens",
    "cathedral": "Stonehallow Minster",
    "citadel": "The Star Citadel",
    "camp": "Camp of the Iron Host",
    "amphitheatre": "The Great Auditorium",
    "playhouse": "The Lantern Playhouse",
    "fair": "St. Bartholomew's Fair Field",
    "forest_n": "The Royal Forest",
    "forest_w": "Elderwood",
    "hills": "The Crownback Hills",
    "inn": "The Sleeping Giant",
}

WORLD_SIZE = 4096               # metres per side (4.096 km x 4.096 km = 16.8 square km)
HEIGHT_RANGE = 256.0            # metres represented by the full 16-bit heightmap range
SEA_LEVEL = 20.0                # metres; everything below is sea
