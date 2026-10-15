"""Personalise the city here, then run `python3 build.py` again.

Every name below flows into the blueprint sheets, the 3D model's object names
and the placement data, so renaming a place here renames it everywhere.
"""

SEED = 1331                     # change for different houses, residents, trees and terrain noise

REALM = "Stonehallow"           # the city
REALM_TAGLINE = "The crowned city that grew around the oldest stones in the world"
YOU = "The Warden of the Stones"   # you: keeper of the ancient precinct
YOUR_HOUSE = "Wardenhouse"         # your home, at the gate of the henge

NAMES = {
    "castle": "Crownhold",
    "keep": "The Crown Tower",
    "henge": "The Hallowstones",
    "avenue": "The Serpent Avenue",
    "cove": "The Cove",
    "obelisk": "The Obelisk",
    "long_barrow": "The Giant's Barrow",
    "dolmen": "The Three Kings' Table",
    "barrows": "The Field of Mounds",
    "needle": "The Needle",
    "row": "The Druids' Row",
    "crowning_stone": "The Crowning Stone",
    "cathedral": "Stonehallow Minster",
    "cloth_hall": "The Cloth Hall & Belfry",
    "guildhall": "The Great Guildhall",
    "market": "The Grand Market",
    "fish_market": "Fish Market",
    "hay_market": "Haymarket",
    "corn_market": "Corn Market",
    "cattle_market": "Cattle Fair",
    "old_bridge": "The Old Bridge",
    "mill_bridge": "Mill Bridge",
    "quay": "King's Quay",
    "river": "River Wend",
    "brook": "Hallow Brook",
    "park": "King's Park",
    "gardens": "The Queen's Gardens",
    "maze": "The Queen's Maze",
    "university": "Collegium of the Seven Stars",
    "physic_garden": "Physic Garden",
    "abbey": "Whitecross Abbey",
    "hospital": "Hospital of St. Brigid",
    "friary_w": "Greyfriars",
    "friary_e": "Blackfriars",
    "column": "The King's Column",
    "crown_square": "Crown Square",
    "forest_n": "The Royal Forest",
    "forest_se": "Thornwood",
    "forest_sw": "Elderwood",
    "hills": "The Crownback Hills",
    "inn": "The Sleeping Giant",
}

WORLD_SIZE = 2048               # metres per side (2.048 km x 2.048 km)
HEIGHT_RANGE = 256.0            # metres represented by the full 16-bit heightmap range
