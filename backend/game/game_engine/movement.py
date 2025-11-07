from game.game_engine.notifier import Notifier

class MovementEngine:
    """
    Handles movement rules between rooms.
    """

    def __init__(self, board):
        self.board = board
        # Track which hallways are occupied: {name: player or None}
        self.hallway_occupancy = {}

    def is_hallway(self, location):
        return location.startswith("Hallway between")

    def hallway_is_occupied(self, hallway):
        return self.hallway_occupancy.get(hallway) is not None

    def can_move(self, player, destination):
        # Prevent hallway→hallway moves
        if self.is_hallway(player.current_room) and self.is_hallway(destination):
            return False

        # Prevent entering occupied hallway
        if self.is_hallway(destination) and self.hallway_is_occupied(destination):
            return False

        # Allow secret passage
        if destination == self.board.SECRET_PASSAGES.get(player.current_room):
            return True

        # Normal adjacency
        return destination in self.board.get_adjacent_rooms(player.current_room)

    def move(self, player, destination):
        if not self.can_move(player, destination):
            Notifier.broadcast(f"🚫 {player.name} cannot move to {destination} (blocked or invalid).")
            return False

        # Clear old hallway occupancy
        if self.is_hallway(player.current_room):
            self.hallway_occupancy[player.current_room] = None

        # Mark new hallway as occupied
        if self.is_hallway(destination):
            self.hallway_occupancy[destination] = player.name

        Notifier.broadcast(f"{player.name} moved from {player.current_room} → {destination}")
        player.current_room = destination
        player.moved_by_suggestion = False
        return True