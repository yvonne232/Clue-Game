from game.game_engine.notifier import Notifier

class TurnManager:
    """Keeps track of whose turn it is and advances turn order."""

    def __init__(self, players):
        self.players = players
        self.current_index = 0

    def current_player(self):
        if not self.players:
            return None
        return self.players[self.current_index]

    def next_turn(self):
        """Advance to the next active (non-eliminated) player."""
        if not self.players:
            return None

        starting_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.players)
            p = self.players[self.current_index]
            if not p.is_eliminated:
                Notifier.broadcast(f"🔄 Next turn: {p.character_card.name}")
                return p
            if self.current_index == starting_index:
                Notifier.broadcast("⚠️ No active players remaining.")
                return None
