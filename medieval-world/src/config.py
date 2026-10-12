"""Personalise your world here, then run `python3 build.py` again.

Every name below flows into the blueprint sheets, the 3D model's object names
and the placement data, so renaming a place here renames it everywhere.
"""

SEED = 1247                     # change for different trees, houses and terrain noise

REALM = "Ashford Vale"          # the name of the whole valley
REALM_TAGLINE = "Where the old ford became a kingdom's heart"
YOU = "The Steward"             # you: the person who keeps this vale
YOUR_HOUSE = "Steward's Hall"   # your home on the market square

NAMES = {
    "castle": "Ashford Castle",
    "town": "Ashford",
    "west_village": "Westbrook",
    "east_village": "Eastmere",
    "south_hamlet": "Southfold",
    "river": "River Ash",
    "brook": "West Brook",
    "mere": "Eastmere Water",
    "abbey": "St. Hilda's Abbey",
    "church": "St. Michael's Church",
    "inn": "The Ford & Crown",
    "village_inn": "The Wheatsheaf",
    "mere_inn": "The Heron",
    "north_hills": "The Greycrown Hills",
    "peak_nw": "Raven Hill",
    "peak_n": "Greycrown",
    "peak_ne": "Beacon Hill",
    "peak_w": "West Tor",
    "spur_w": "Hound's Spur",
    "spur_e": "Quarry Spur",
    "forest_nw": "The Wildwood",
    "forest_ne": "King's Chase",
    "forest_sw": "Southwood",
    "stones": "The Nine Maidens",
    "ford": "The Old Ash Ford",
    "bridge_s": "Ash Bridge",
    "bridge_e": "East Bridge",
    "lodge": "King's Chase Lodge",
}

WORLD_SIZE = 2048               # metres per side (the map is 2.048 km x 2.048 km)
HEIGHT_RANGE = 256.0            # metres represented by the full 16-bit heightmap range
