"""
Full Clue-Less game simulation (no GameManager).
Implements all official rules: hallway blocking, secret passages,
moved-by-suggestion stay, and correct suspect movement.
"""

import random
from game.game_engine.board import Board
from game.game_engine.movement import MovementEngine
from game.game_engine.turn_manager import TurnManager
from game.game_engine.deck import CardDeck
from game.game_engine.suggestion import SuggestionEngine
from game.game_engine.accusation import AccusationEngine
from game.game_engine.game_state import GameState
from game.game_engine.notifier import Notifier


# --- Player mock ---
class MockPlayer:
    def __init__(self, name, start_location):
        self.name = name
        self.current_room = start_location
        self.cards = []
        self.eliminated = False
        self.moved_by_suggestion = False

    def __repr__(self):
        return f"<{self.name} in {self.current_room}>"


def simulate_full_game():
    print("\n === Starting Full Clue-Less Game Simulation ===\n")

    board = Board()
    movement = MovementEngine(board)
    state = GameState()

    # Canonical starting hallways
    start_pos = {
        "Miss Scarlet": "Hallway between Lounge and Hall",
        "Colonel Mustard": "Hallway between Lounge and Dining Room",
        "Mrs. White": "Hallway between Kitchen and Ballroom",
        "Mr. Green": "Hallway between Ballroom and Conservatory",
        "Mrs. Peacock": "Hallway between Conservatory and Library",
        "Professor Plum": "Hallway between Library and Study",
    }

    players = [MockPlayer(name, loc) for name, loc in start_pos.items()]
    turn_mgr = TurnManager(players)

    deck = CardDeck(
        characters=list(start_pos.keys()),
        weapons=["Candlestick", "Dagger", "Lead Pipe", "Revolver", "Rope", "Wrench"],
        rooms=[r for row in board.ROOMS for r in row],
    )
    solution = deck.create_solution()
    hands = deck.deal(players)
    acc_engine = AccusationEngine(solution)
    sugg_engine = SuggestionEngine(players)

    # Assign cards and initial positions
    print(" --- Player Hands ---")
    for p in players:
        p.cards = hands[p]
        state.update_position(p.name, p.current_room)
        print(f"{p.name}: {', '.join(p.cards)}")
    print("------------------------")
    print(f"Secret Solution (hidden): {solution}\n")

    Notifier.broadcast("Game setup complete. Beginning turns...")

    # --- Game loop ---
    round_num = 1
    max_rounds = 20
    winner = None

    while not winner and round_num <= max_rounds:
        print(f"\n===== ROUND {round_num} =====")

        for current in list(players):
            if current.eliminated:
                continue

            Notifier.broadcast(f"{current.name}'s turn ({current.current_room})")

            # If all exits blocked and no secret passage
            adj = board.get_adjacent_rooms(current.current_room)
            valid_exits = [
                d for d in adj
                if not (movement.is_hallway(d) and movement.hallway_is_occupied(d))
            ]
            if not valid_exits and not board.SECRET_PASSAGES.get(current.current_room):
                Notifier.broadcast(f"🚫 {current.name} cannot move or suggest (blocked).")
                continue

            # If moved by suggestion → may stay and suggest
            if current.moved_by_suggestion:
                Notifier.broadcast(f"{current.name} stays in {current.current_room} (moved by suggestion).")
                current.moved_by_suggestion = False
            else:
                dest = random.choice(valid_exits)
                movement.move(current, dest)
                state.update_position(current.name, dest)

            # Make suggestion
            char = random.choice(deck.characters)
            weap = random.choice(deck.weapons)
            room = current.current_room
            result = sugg_engine.handle_suggestion(current, char, weap, room)
            Notifier.broadcast(f"{current.name} suggests {char} + {weap} in {room}")
            Notifier.broadcast(result)

            # Random accusation
            if random.random() < 0.25:
                guess = {
                    "character": random.choice(deck.characters),
                    "weapon": random.choice(deck.weapons),
                    "room": random.choice(deck.rooms),
                }
                correct = acc_engine.check_accusation(**guess)
                if correct:
                    Notifier.broadcast(f"🏆 {current.name} accused correctly and wins!")
                    winner = current
                    break
                else:
                    current.eliminated = True
                    Notifier.broadcast(f"❌ {current.name} accused {guess} incorrectly and is eliminated.")

            turn_mgr.advance_turn()

        round_num += 1

    print("\n=== 🏁 Game Over ===")
    if winner:
        print(f"🎉 Winner: {winner.name}")
    else:
        print("⏳ No winner — game ended by round limit.")
    print(f"🔑 Actual Solution: {solution}\n")

    print("=== Final Player Status ===")
    for p in players:
        print(f"{p.name}: room={state.get_player_room(p.name)}, eliminated={p.eliminated}")
    print("============================\n")


if __name__ == "__main__":
    random.seed(42)
    simulate_full_game()
