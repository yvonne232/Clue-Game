from game.game_engine.game_manager import GameManager
from game.game_engine.notifier import Notifier
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

def run_full_simulation():
    Notifier.broadcast("🎲 === Starting Full Clue-Less Game Simulation ===")

    game = GameManager()

    Notifier.broadcast("\n --- Player Hands ---")
    for p in game.players:
        Notifier.broadcast(f"{p['name']}: " + ", ".join(p["hand"]))
    Notifier.broadcast("------------------------")

    game.run_game()

if __name__ == "__main__":
    run_full_simulation()
