import random
from game.game_engine.notifier import Notifier

class SuggestionEngine:
    """
    Handles making and disproving suggestions.
    """

    def __init__(self, players):
        self.players = players

    def handle_suggestion(self, suggester, character, weapon, room):
        # Move suspect to suggested room
        suspect = next((p for p in self.players if p.name == character), None)
        if suspect and not suspect.eliminated:
            suspect.current_room = room
            suspect.moved_by_suggestion = True
            Notifier.broadcast(f"{suspect.name} was moved to {room} by suggestion.")

        # Check for disproofs
        others = [p for p in self.players if p != suggester and not p.eliminated]
        random.shuffle(others)
        for p in others:
            matching = [c for c in p.cards if c in (character, weapon, room)]
            if matching:
                card = random.choice(matching)
                return f"{p.name} can disprove with {card}"
        return "No one can disprove the suggestion."
