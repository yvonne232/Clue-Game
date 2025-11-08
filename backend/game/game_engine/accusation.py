# game/game_engine/accusation.py
from game.game_engine.notifier import Notifier

class AccusationEngine:
    """Handles accusation logic — can be made any time."""

    def __init__(self, solution):
        self.solution = solution

    def check_accusation(self, suspect, weapon, room):
        correct = (
            self.solution["suspect"] == suspect
            and self.solution["weapon"] == weapon
            and self.solution["room"] == room
        )
        if correct:
            Notifier.broadcast("✅ Correct accusation!")
        else:
            Notifier.broadcast("❌ Wrong accusation.")
        return correct
