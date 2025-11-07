"""
Integration test: simulate a mini Clue-Less game round using the game engine.
"""

from game.game_engine.board import Board
from game.game_engine.movement import MovementEngine
from game.game_engine.turn_manager import TurnManager
from game.game_engine.deck import CardDeck   
from game.game_engine.suggestion import SuggestionEngine
from game.game_engine.accusation import AccusationEngine
from game.game_engine.game_state import GameState
from game.game_engine.notifier import Notifier


class MockPlayer:
    def __init__(self, name, room="Study"):
        self.name = name
        self.current_room = room
        self.cards = []

    def __repr__(self):
        return f"<Player {self.name} in {self.current_room}>"


def simulate_game():
    print("\n=== Simulating Mini Clue-Less Game Round ===")

    # --- Setup ---
    board = Board()
    movement = MovementEngine(board)
    players = [MockPlayer("Alice"), MockPlayer("Bob"), MockPlayer("Carol")]
    turn_mgr = TurnManager(players)
    deck = CardDeck(
        characters=["Miss Scarlet", "Colonel Mustard", "Professor Plum"],
        weapons=["Rope", "Candlestick", "Knife"],
        rooms=["Study", "Hall", "Lounge", "Library", "Kitchen"],
    )

    solution = deck.create_solution()
    accusation_engine = AccusationEngine(solution)
    hands = deck.deal(players)
    state = GameState()

    # Assign cards and show them
    print("\n --- Player Cards ---")
    for p in players:
        p.cards = hands[p]
        state.update_position(p.name, p.current_room)
        print(f"{p.name}'s cards: {', '.join(p.cards)}")
    print("-----------------------\n")

    sugg_engine = SuggestionEngine(players)
    Notifier.broadcast(f"Game started with secret solution: {solution}")

    # --- Play 3 turns ---
    for _ in range(3):
        current = turn_mgr.get_current_player()
        Notifier.broadcast(f"→ {current.name}'s turn in {current.current_room}")

        # Try to move to the first adjacent room
        adj = board.get_adjacent_rooms(current.current_room)
        if adj:
            dest = adj[0]
            if movement.move(current, dest):
                state.update_position(current.name, dest)
                Notifier.broadcast(f"{current.name} moved to {dest}")

        # Make a suggestion
        sugg = sugg_engine.handle_suggestion(current, "Miss Scarlet", "Rope", current.current_room)
        Notifier.broadcast(f"{current.name} suggests Scarlet + Rope in {current.current_room}")
        Notifier.broadcast(sugg)

        # On the last turn, make an accusation
        if _ == 2:
            guess = {"character": "Miss Scarlet", "weapon": "Rope", "room": current.current_room}
            ok = accusation_engine.check_accusation(**guess)
            Notifier.broadcast(f"{current.name} accuses {guess} → {'✅ Correct!' if ok else '❌ Wrong!'}")

        turn_mgr.advance_turn()

    # --- End of game ---
    print("\n=== Final Positions ===")
    for p in players:
        print(f"{p.name}: {state.get_player_room(p.name)}")
    print("=== Game Simulation Complete ===\n")


if __name__ == "__main__":
    simulate_game()
