# player.py
# Purpose: Maintains the data associated with a player and their capabilities.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional
from .cards import Card             # each player has hand containing Card objects
from .enums import CardKind         # identifies type of each card
from .suggestion import Suggestion
#from .board import Location

@dataclass
class Player:
    """ Represents a single player. """

    id: str     # unique player ID
    name: str   # Player's display name
    character: Optional[str] = None         # chosen character/suspect 
    position: Optional[str] = None          # current board location (Room or Hallway)
    hand: List[Card] = field(default_factory = list)    # list of Card objects dealt to this player
    is_lost: bool = False                    # whether player has lost by incorrect accusation

    lookup: ClassVar[Dict[str, "Player"]] = {}          # static map for player ID lookups


    def __post_init__(self):
        """ Register player in static loopkup map when created """
        Player.lookup[self.id] = self


    def can_disprove(self, s: "Suggestion") -> List[Card]:
        """ Given a Suggestion object, determines which cards in this player's hands can disprove (match at least one suggestion card)"""

        matches: List[Card] = []
        
        # iterate through player's hand, compare each card to suggestion cards
        for c in self.hand:
            if (c.kind == s.suspect.kind and c.name == s.suspect.name) \
                or (c.kind == s.weapon.kind and c.name == s.weapon.name) \
                or (c.kind == s.room.kind and c.name == s.room.name):
                matches.append(c)
        return matches
    

    @classmethod
    def get_player(cls, player_id: str) -> "Player":
        """ Retrieves a Player instance by ID using static lookup map """
        
        if player_id not in cls.lookup:
            raise KeyError(f"No Player with ID '{player_id}' exists.")
        return cls.lookup[player_id]
    
