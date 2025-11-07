class GameState:
    """
    Tracks positions and card ownership.
    """

    def __init__(self):
        self.positions = {}  # player_name → room_name
        self.hallway_occupancy = {}

    def update_position(self, player_name, location):
        self.positions[player_name] = location

    def get_player_room(self, player_name):
        return self.positions.get(player_name)
