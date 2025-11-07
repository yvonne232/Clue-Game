class Board:
    """
    Defines the 3×3 Clue-Less room layout, hallways between rooms,
    and secret passages. Provides adjacency lookups for movement.
    """

    ROOMS = [
        ["Study", "Hall", "Lounge"],
        ["Library", "Billiard Room", "Dining Room"],
        ["Conservatory", "Ballroom", "Kitchen"],
    ]

    # Diagonal secret passages
    SECRET_PASSAGES = {
        "Study": "Kitchen",
        "Kitchen": "Study",
        "Lounge": "Conservatory",
        "Conservatory": "Lounge",
    }

    # Each tuple represents two rooms connected by a hallway
    RAW_HALLWAYS = [
        ("Study", "Hall"),
        ("Hall", "Lounge"),
        ("Study", "Library"),
        ("Hall", "Billiard Room"),
        ("Lounge", "Dining Room"),
        ("Library", "Billiard Room"),
        ("Billiard Room", "Dining Room"),
        ("Library", "Conservatory"),
        ("Billiard Room", "Ballroom"),
        ("Dining Room", "Kitchen"),
        ("Conservatory", "Ballroom"),
        ("Ballroom", "Kitchen"),
    ]

    def __init__(self):
        # Build hallway names (bidirectional)
        self.HALLWAYS = {}
        for r1, r2 in self.RAW_HALLWAYS:
            name1 = f"Hallway between {r1} and {r2}"
            name2 = f"Hallway between {r2} and {r1}"
            self.HALLWAYS[name1] = (r1, r2)
            self.HALLWAYS[name2] = (r1, r2)

        # Build adjacency map
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self):
        adjacency = {room: [] for row in self.ROOMS for room in row}

        # Link rooms and hallways
        for hallway, (r1, r2) in self.HALLWAYS.items():
            adjacency.setdefault(r1, []).append(hallway)
            adjacency.setdefault(r2, []).append(hallway)
            adjacency[hallway] = [r1, r2]

        # Add secret passages
        for r, target in self.SECRET_PASSAGES.items():
            adjacency[r].append(target)

        return adjacency

    def get_adjacent_rooms(self, room_name):
        """Return all rooms/hallways adjacent to a given room or hallway."""
        return self.adjacency.get(room_name, [])

    def all_locations(self):
        """Return a list of all rooms + hallways."""
        return list(self.adjacency.keys())

    def __repr__(self):
        return f"<Board: {len(self.adjacency)} locations>"
