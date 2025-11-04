# state.py
# Purpose: Maintains the attributes of the game that are necessary to keep 
#           the game moving and the game data that isn’t owned by a player

from dataclasses import dataclass, field
from typing import Dict, Optional
from collections import deque
from .player import Player
from .board import Board
from .cards import CaseFile
from .suggestion import Suggestion
from .enums import TurnPhase

