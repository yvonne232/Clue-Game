import random

class CardDeck:
    """
    Manages shuffling and dealing cards.
    """

    def __init__(self, characters, weapons, rooms):
        self.characters = characters
        self.weapons = weapons
        self.rooms = rooms
        self.deck = characters + weapons + rooms

    def create_solution(self):
        return {
            "character": random.choice(self.characters),
            "weapon": random.choice(self.weapons),
            "room": random.choice(self.rooms),
        }


    def deal(self, players):
        """Deal cards evenly to players."""
        cards = self.characters + self.weapons + self.rooms
        random.shuffle(cards)

        # remove solution cards
        hands = {p: [] for p in players}
        while cards:
            for p in players:
                if cards:
                    hands[p].append(cards.pop())
        return hands
