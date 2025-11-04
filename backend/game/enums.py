# enums.py
# Purpose: Defines reusable enumerations for turn phases and card categories

from enum import Enum, auto

class TurnPhase(Enum):
    """ Tracks which stage the game is currently in. """
    LOBBY = auto()                      # waiting for players to join
    AWAIT_MOVE_OR_SUGGEST = auto()      # players turn (can move or suggest)
    MUST_SUGGEST = auto()               # player must suggest if they move into a room
    AWAIT_DISPROVE = auto()             # waiting for next player to disprove suggestion
    TURN_COMPLETE_PENDING_END = auto()  # suggestion resolved, ready for next turn

class CardKind(Enum):
    """ Defines three card types in deck. """
    SUSPECT = auto()
    WEAPON = auto()
    ROOM = auto()