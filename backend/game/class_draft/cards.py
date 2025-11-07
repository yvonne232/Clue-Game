# cards.py
# Purpose: Represents cards that can be dealt to players and which can comprise a solution

from dataclasses import dataclass       # automatically generates boilerplate methods for a class
from typing import List, Dict
import random                           # for shuffling
from .enums import CardKind
from .constants import SUSPECTS, WEAPONS, ROOMS

@dataclass(frozen=True)     # immutable, cards never change once created
class Card:
    """ Represents a single card (suspect, weapon, or room). """
    kind: CardKind      # SUSPECT, WEAPON, or ROOM
    name: str           # card display name
    id: str             # unique card identifier

@dataclass(frozen=True)     # immutable, constant once drawn
class CaseFile:
    """ Secret solution to the mystery (one suspct, one weapon, one room). """
    suspect: Card
    weapon: Card
    room: Card

class Deck:
    """ Handles shuffling, drawing, and dealing cards (not immutable, must change during game play) """
    
    def __init__(self):
        """ Builds cards with ids """
        self.cards: List[Card] = (
            [Card(CardKind.SUSPECT, s, f"S{i}") for i, s in enumerate(SUSPECTS, start = 1)] +
            [Card(CardKind.WEAPON, w, f"W{i}") for i, w in enumerate(WEAPONS, start = 1)] +
            [Card(CardKind.ROOM, r, f"R{i}") for i, r in enumerate(ROOMS, start = 1)]
        )
    
    def shuffle(self) -> None:
        """ Randomize deck order. """
        random.shuffle(self.cards)

    def draw_case_file(self) -> CaseFile:       # this is startGame() in sdd, but this name seems more descriptive
        """ Draws one suspect, weapon, and room to form and return CaseFile, and removes these from the deck. """
        suspect = self._pop_first(CardKind.SUSPECT)
        weapon  = self._pop_first(CardKind.WEAPON)
        room    = self._pop_first(CardKind.ROOM)
        return CaseFile(suspect, weapon, room)
    
    def deal(self, hands: Dict[str, list]) -> None:
        """ Deals remaining cards evenly among all players (round-robin). """
        ids = list(hands.keys())
        i = 0
        while self.cards:
            hands[ids[i % len(ids)]].append(self.cards.pop())
            i +=1

    def _pop_first(self, kind: CardKind) -> Card:
        """ Helper function for draw_case_file() to remove and return the first card of a given kind. """
        for i, c in enumerate(self.cards):
            if c.kind == kind:
                return self.cards.pop(i)
        raise ValueError(f"No card of kind {kind} left in the deck")

