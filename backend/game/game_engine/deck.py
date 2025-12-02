import random

from game.game_engine.constants import ROOMS, SUSPECTS, WEAPONS
from game.models import Card, Game, Solution


class Deck:
    """Handles loading cards, creating the mystery solution, and dealing hands."""

    def __init__(self):
        """Initialize deck by ensuring all required cards exist and loading them."""
        self._ensure_cards_exist()
        
        # Load cards grouped by type
        self.characters = list(Card.objects.filter(card_type="CHAR"))
        self.weapons = list(Card.objects.filter(card_type="WEAP"))
        self.rooms = list(Card.objects.filter(card_type="ROOM"))

        # Verify card counts
        expected_counts = {
            "CHAR": len(SUSPECTS),
            "WEAP": len(WEAPONS),
            "ROOM": len(ROOMS),
        }
        actual_counts = {
            "CHAR": len(self.characters),
            "WEAP": len(self.weapons),
            "ROOM": len(self.rooms),
        }
        if any(actual_counts[key] != expected_counts[key] for key in actual_counts):
            raise RuntimeError(
                f"Card count mismatch. Expected: {expected_counts}, Got: {actual_counts}"
            )

        self.all_cards = self.characters + self.weapons + self.rooms
        
    def _ensure_cards_exist(self):
        """Ensure all required cards exist in the database."""
        card_data = (
            [(name, "CHAR") for name in SUSPECTS]
            + [(name, "WEAP") for name in WEAPONS]
            + [(name, "ROOM") for name in ROOMS]
        )

        for name, card_type in card_data:
            Card.objects.get_or_create(
                name=name,
                defaults={"card_type": card_type},
            )

    def create_solution(self):
        """Randomly select one character, weapon, and room for the mystery."""
        char = random.choice(self.characters)
        weapon = random.choice(self.weapons)
        room = random.choice(self.rooms)

        Game.objects.update(solution=None)
        Solution.objects.all().delete()
        return Solution.objects.create(character=char, weapon=weapon, room=room)

    def deal(self, num_players):
        """Deal remaining (non-solution) cards evenly among players."""
        latest_solution = Solution.objects.order_by("-created_at").first()

        cards_to_deal = self.all_cards.copy()
        if latest_solution:
            excluded = {
                latest_solution.character_id,
                latest_solution.weapon_id,
                latest_solution.room_id,
                }
            cards_to_deal = [card for card in cards_to_deal if card.id not in excluded]

        random.shuffle(cards_to_deal)
        hands = [[] for _ in range(num_players)]
        for index, card in enumerate(cards_to_deal):
            hands[index % num_players].append(card.name)
        return hands
