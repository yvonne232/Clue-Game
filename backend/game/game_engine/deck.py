import random
from game.models import Card, Solution, Game


class Deck:
    """Handles loading cards, creating the mystery solution, and dealing hands."""

    def __init__(self):
        """Initialize deck by ensuring all required cards exist and loading them."""
        from game.class_draft.constants import SUSPECTS, WEAPONS, ROOMS

        # Seed cards if they don't exist
        self._ensure_cards_exist()
        
        # Load cards grouped by type
        self.characters = list(Card.objects.filter(card_type="CHAR"))
        self.weapons = list(Card.objects.filter(card_type="WEAP"))
        self.rooms = list(Card.objects.filter(card_type="ROOM"))

        # Verify card counts
        expected_counts = {
            'CHAR': len(SUSPECTS),
            'WEAP': len(WEAPONS),
            'ROOM': len(ROOMS)
        }
        
        actual_counts = {
            'CHAR': len(self.characters),
            'WEAP': len(self.weapons),
            'ROOM': len(self.rooms)
        }
        
        if any(actual_counts[type] != expected_counts[type] for type in actual_counts):
            raise RuntimeError(f"Card count mismatch. Expected: {expected_counts}, Got: {actual_counts}")

        # Store all cards together for convenience
        self.all_cards = self.characters + self.weapons + self.rooms
        
    def _ensure_cards_exist(self):
        """Ensure all required cards exist in the database."""
        SUSPECTS = [
            "Miss Scarlet",
            "Colonel Mustard",
            "Mrs. White",
            "Mr. Green",
            "Mrs. Peacock",
            "Professor Plum"
        ]

        WEAPONS = [
            "Candlestick",
            "Knife",
            "Lead Pipe",
            "Revolver",
            "Rope",
            "Wrench"
        ]

        ROOMS = [
            "Kitchen",
            "Ballroom",
            "Conservatory",
            "Dining Room",
            "Billiard Room",
            "Library",
            "Lounge",
            "Hall",
            "Study"
        ]
        
        card_data = [
            (name, 'CHAR') for name in SUSPECTS
        ] + [
            (name, 'WEAP') for name in WEAPONS
        ] + [
            (name, 'ROOM') for name in ROOMS
        ]

        for name, card_type in card_data:
            Card.objects.get_or_create(
                name=name,
                defaults={'card_type': card_type}
            )

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
