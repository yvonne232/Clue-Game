class TurnManager:
    """
    Controls turn order and rotation.
    """

    def __init__(self, players):
        self.players = players
        self.current_index = 0 

    def get_current_player(self):
        return self.players[self.current_index]

    def advance_turn(self):
        n = len(self.players)
        for _ in range(n):
            self.current_index = (self.current_index + 1) % n
            if not self.players[self.current_index].eliminated:
                return self.players[self.current_index]
        return None  # everyone eliminated
