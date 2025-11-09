import random
from game.models import Card, Solution, Game


class Deck:
    """Handles loading cards, creating the mystery solution, and dealing hands."""

    def __init__(self):
        """Ensure all cards exist and load them grouped by type."""
        self.characters = list(Card.objects.filter(card_type="CHAR"))
        self.weapons = list(Card.objects.filter(card_type="WEAP"))
        self.rooms = list(Card.objects.filter(card_type="ROOM"))

        if not (self.characters and self.weapons and self.rooms):
            raise RuntimeError("❌ Missing cards in database — run migrations to create default cards.")

        # Store all cards together for convenience
        self.all_cards = self.characters + self.weapons + self.rooms

    # ------------------------------------------------------------
    #  Create or load the mystery solution
    # ------------------------------------------------------------
    def create_solution(self):
        """Randomly select one character, weapon, and room for the mystery."""

        char = random.choice(self.characters)
        weap = random.choice(self.weapons)
        room = random.choice(self.rooms)

        Game.objects.update(solution=None)
        Solution.objects.all().delete()
        return Solution.objects.create(character=char, weapon=weap, room=room)

    # ------------------------------------------------------------
    #  Deal cards evenly among players
    # ------------------------------------------------------------
    def deal(self, num_players):
        """Deal remaining (non-solution) cards evenly among players."""
        latest_solution = Solution.objects.order_by("-created_at").first()

        cards_to_deal = self.all_cards.copy()
        if latest_solution:
            cards_to_deal = [
                c for c in cards_to_deal
                if c.id not in {
                    latest_solution.character.id,
                    latest_solution.weapon.id,
                    latest_solution.room.id,
                }
            ]

        random.shuffle(cards_to_deal)
        hands = [[] for _ in range(num_players)]
        for i, card in enumerate(cards_to_deal):
            hands[i % num_players].append(card.name)
        return hands
