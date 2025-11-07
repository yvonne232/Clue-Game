"""
Defines the 3×3 Clue-Less board layout and adjacency logic.
"""

class BoardLayout:
    # 3×3 room grid
    ROOMS = [
        ["Study", "Hall", "Lounge"],
        ["Library", "Billiard Room", "Dining Room"],
        ["Conservatory", "Ballroom", "Kitchen"],
    ]

    # Secret passages (corner to corner)
    SECRET_PASSAGES = {
        "Study": "Kitchen",
        "Kitchen": "Study",
        "Lounge": "Conservatory",
        "Conservatory": "Lounge",
    }

    def __init__(self):
        """Build adjacency relationships between rooms."""
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self):
        adjacency = {}
        for i, row in enumerate(self.ROOMS):
            for j, room in enumerate(row):
                adjacent = []
                if i > 0:
                    adjacent.append(self.ROOMS[i - 1][j])
                if i < 2:
                    adjacent.append(self.ROOMS[i + 1][j])
                if j > 0:
                    adjacent.append(self.ROOMS[i][j - 1])
                if j < 2:
                    adjacent.append(self.ROOMS[i][j + 1])
                if room in self.SECRET_PASSAGES:
                    adjacent.append(self.SECRET_PASSAGES[room])
                adjacency[room] = adjacent
        return adjacency

    def get_adjacent_rooms(self, room_name):
        """Return all adjacent or passage-connected rooms."""
        return self.adjacency.get(room_name, [])
