# game/game_engine/accusation.py
from game.game_engine.notifier import Notifier


class AccusationEngine:
    """Handles accusation logic — can be made any time."""

    def __init__(self, solution, room_name="default"):
        self.solution = solution
        self.room_name = room_name

    def check_accusation(self, suspect, weapon, room):
        correct = (
            self.solution["suspect"] == suspect
            and self.solution["weapon"] == weapon
            and self.solution["room"] == room
        )
        if correct:
            Notifier.broadcast("✅ Correct accusation!", room=self.room_name)
        else:
            Notifier.broadcast("❌ Wrong accusation.", room=self.room_name)
        return correct
