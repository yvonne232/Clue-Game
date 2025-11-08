from django.core.management.base import BaseCommand
from game.game_engine.game_manager import GameManager

class Command(BaseCommand):
    help = "Run the full Clue-Less simulation with reasoning"

    def handle(self, *args, **options):
        gm = GameManager(game_name="default")
        gm.run_game(max_rounds=20)