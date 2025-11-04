# suggestion.py
# Purpose: Stores live suggestion context during a turn

from dataclasses import dataclass
from typing import Dict, List
from .enums import CardKind
from .cards import Card, CaseFile
from .player import Player

class Suggestion:
    suggesterId: str        # player who made teh suggestion
    suspect: Card           # suggested suspect
    weapon: Card            # suggested weapon
    room: Card              # suggested room
    isAccusation: bool = False  # whether this is an accusation (not just a suggestion)

