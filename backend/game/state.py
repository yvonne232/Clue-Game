# state.py
# Purpose: Maintains the attributes of the game that are necessary to keep 
#           the game moving and the game data that isn’t owned by a player

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING
from .board import Board
from .cards import CaseFile
from .suggestion import Suggestion
from .enums import TurnPhase

if TYPE_CHECKING:
    from .player import Player

@dataclass
class GameState:
    """ Represents the current snapshot of all data, including player positions, collected clues, and turn order."""

    # Optional because not all parts of game state will exist at the same time

    players: Dict[str, Player] = field(default_factory=dict)                # all players currently in game (dict bc set can contain mutable class)
    turn_order: List[str] = field(default_factory=list)                  # ordered queue of player IDs, represents player sequence
    board: Optional[Board] = None               # game board with rooms and hallways
    solution: Optional[CaseFile] = None         # hidden solution
    current_player_id: Optional[str] = None     # ID of the player whose turn it is
    pending_suggestion: Optional[Suggestion] = None   # active suggestion being resolved


    def add_player(self, player: Player) -> None:
        """
        Add a player to the game state.
        IDs must be unique; raises ValueError on duplicate.
        """
        if player.id in self.players:
            raise ValueError(f"Player with id {player.id} already exists.")
        self.players[player.id] = player


    def get_player(self, player_id: str) -> Player:
        """
        Retrieve a player by ID from the game state's player dictionary.
        Raises KeyError if not found.
        """
        if player_id not in self.players:
            raise KeyError(f"Player {player_id} not found in game state.")
        return self.players[player_id]

    def view_for_broadcast(self) -> dict:
        """ convert internal state to JSON for frontend display. """

        current_player = None
        if self.current_player_id and self.current_player_id in self.players:
            cp = self.players[self.current_player_id]
            current_player = {
                "id": cp.id,
                "name": cp.name,
                "character": cp.character,
            }

        return {
            # list players
            "players": [
                {
                    "name": p.name,
                    "character": p.character,
                    "position": p.position
                }
                for p in self.players.values()
            ],

            # display current player & turn order
            "Current Player": current_player,
            "Turn Order": list(self.turn_order)
        }