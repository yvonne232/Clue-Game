"""Centralized static data for the Clue-Less game."""

SUSPECTS = [
    "Miss Scarlet",
    "Colonel Mustard",
    "Mrs. White",
    "Mr. Green",
    "Mrs. Peacock",
    "Professor Plum",
]

WEAPONS = [
    "Candlestick",
    "Knife",
    "Lead Pipe",
    "Revolver",
    "Rope",
    "Wrench",
]

ROOMS = [
    "Kitchen",
    "Ballroom",
    "Conservatory",
    "Dining Room",
    "Billiard Room",
    "Library",
    "Lounge",
    "Hall",
    "Study",
]

# ---------------------------------------------------------------------------
# Board definitions
# ---------------------------------------------------------------------------

ROOM_DEFINITIONS = {
    "R00": {"name": "Kitchen", "hallways": ["H01", "H03"], "secret_passage": "R22"},
    "R01": {"name": "Ballroom", "hallways": ["H01", "H02", "H04"], "secret_passage": None},
    "R02": {"name": "Conservatory", "hallways": ["H02", "H05"], "secret_passage": "R20"},
    "R10": {"name": "Dining Room", "hallways": ["H03", "H06", "H08"], "secret_passage": None},
    "R11": {"name": "Billiard Room", "hallways": ["H04", "H06", "H07", "H09"], "secret_passage": None},
    "R12": {"name": "Library", "hallways": ["H05", "H07", "H10"], "secret_passage": None},
    "R20": {"name": "Lounge", "hallways": ["H08", "H11"], "secret_passage": "R02"},
    "R21": {"name": "Hall", "hallways": ["H09", "H11", "H12"], "secret_passage": None},
    "R22": {"name": "Study", "hallways": ["H10", "H12"], "secret_passage": "R00"},
}

HALLWAY_DEFINITIONS = {
    "H01": {
        "name": "H01 - Between Kitchen and Ballroom",
        "room1": "R00",
        "room2": "R01",
    },
    "H02": {
        "name": "H02 - Between Ballroom and Conservatory",
        "room1": "R01",
        "room2": "R02",
    },
    "H03": {
        "name": "H03 - Between Kitchen and Dining Room",
        "room1": "R00",
        "room2": "R10",
    },
    "H04": {
        "name": "H04 - Between Ballroom and Billiard Room",
        "room1": "R01",
        "room2": "R11",
    },
    "H05": {
        "name": "H05 - Between Conservatory and Library",
        "room1": "R02",
        "room2": "R12",
    },
    "H06": {
        "name": "H06 - Between Dining Room and Billiard Room",
        "room1": "R10",
        "room2": "R11",
    },
    "H07": {
        "name": "H07 - Between Billiard Room and Library",
        "room1": "R11",
        "room2": "R12",
    },
    "H08": {
        "name": "H08 - Between Dining Room and Lounge",
        "room1": "R10",
        "room2": "R20",
    },
    "H09": {
        "name": "H09 - Between Billiard Room and Hall",
        "room1": "R11",
        "room2": "R21",
    },
    "H10": {
        "name": "H10 - Between Library and Study",
        "room1": "R12",
        "room2": "R22",
    },
    "H11": {
        "name": "H11 - Between Lounge and Hall",
        "room1": "R20",
        "room2": "R21",
    },
    "H12": {
        "name": "H12 - Between Hall and Study",
        "room1": "R21",
        "room2": "R22",
    },
}

# ---------------------------------------------------------------------------
# Player starting positions (map character → hallway code)
# ---------------------------------------------------------------------------

STARTING_POSITIONS = {
    "Miss Scarlet": "H11",
    "Colonel Mustard": "H08",
    "Professor Plum": "H10",
    "Mrs. Peacock": "H05",
    "Mr. Green": "H02",
    "Mrs. White": "H01",
}