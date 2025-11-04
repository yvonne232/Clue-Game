# manager.py
# Purpose: Controller
#   - orchestrate game lifecycle
#   - validate and apply actions 
#   - route events (broadcast/private)
#   - manage turn flow

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence
from .state import GameState
from .cards import Deck
from .player import Player

class Manager:
    """ Represents game controller """
    
    lobby_id: str       # identifier for running game instance
    state: GameState    # authoritative game state controller
    deck: Deck          # shuffled deck used to draw case file and deal hands

    def join_lobby(self, player: Player) -> Player:
        """
        Pre: Game not started; capacity < 6; character selection remains 
        Post: Player added to state.players; broadcast lobby update 
        """

    def start_game() -> None:
        """
        Pre: 2 ≤ players ≤ 6; game not started 
        Effects:  
            deck.shuffle() 
            state.solution = deck.startGame() 
            deck.deal(players) 
            Set turnOrder and currentPlayerId 
            Broadcast gameStarted event 
        """
    