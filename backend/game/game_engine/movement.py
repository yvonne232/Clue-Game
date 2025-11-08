# game/game_engine/movement.py
from game.game_engine.notifier import Notifier

class MovementEngine:
    """Handles room/hallway movement logic and occupancy rules."""

    def __init__(self):
        self.occupied_hallways = set()

    def is_hallway(self, name):
        return "Hallway" in name

    def hallway_is_occupied(self, hallway_name):
        return hallway_name in self.occupied_hallways

    def move(self, player, dest):
        """Move player and track hallway occupancy."""
        prev = player["location"]

        # Free previous hallway
        if self.is_hallway(prev) and prev in self.occupied_hallways:
            self.occupied_hallways.remove(prev)

        # Check destination
        if self.is_hallway(dest):
            if dest in self.occupied_hallways:
                Notifier.broadcast(f" {player['name']} cannot move to occupied {dest}.")
                return False
            self.occupied_hallways.add(dest)

        player["location"] = dest
        Notifier.broadcast(f"{player['name']} moved to {dest}")
        return True
