# game/game_engine/game_state.py
class GameState:
    """
    Tracks player positions, known cards, and game progress.
    """

    def __init__(self, players, deck):
        self.players = players
        self.deck = deck
        self.positions = {p["name"]: p["location"] for p in players}
        self.eliminated = {p["name"]: False for p in players}
        self.known_cards = {p["name"]: set(p["hand"]) for p in players}

    def update_position(self, player_name, new_location):
        self.positions[player_name] = new_location

    def get_player_room(self, player_name):
        return self.positions.get(player_name, "Unknown")

    def mark_eliminated(self, player_name):
        self.eliminated[player_name] = True

    def is_eliminated(self, player_name):
        return self.eliminated.get(player_name, False)

    def reveal_card(self, player_name, card):
        """Track that this player has shown this card."""
        if player_name in self.known_cards:
            self.known_cards[player_name].add(card)

    def summary(self):
        """Return formatted summary for debugging/logging."""
        summary_lines = []
        for p in self.players:
            name = p["name"]
            loc = self.positions[name]
            elim = "❌" if self.eliminated[name] else "✅"
            summary_lines.append(f"{name}: {loc} ({elim})")
        return "\n".join(summary_lines)
