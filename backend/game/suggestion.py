# suggestion.py
# Purpose: Stores live suggestion context during a turn

from dataclasses import dataclass
from typing import Optional
from .cards import Card, CaseFile

@dataclass
class Suggestion:
    """ Represent single suggestoin during a player's turn. """
    suggester_id: str        # player who made the suggestion
    suspect: Card           # suggested suspect
    weapon: Card            # suggested weapon
    room: Card              # suggested room
    is_accusation: bool = False  # whether this is an accusation (not just a suggestion)


