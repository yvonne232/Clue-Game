# manager.py
# Purpose: Controller
#   - orchestrate game lifecycle
#   - validate and apply actions 
#   - route events (broadcast/private)
#   - manage turn flow

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4
from .state import GameState
from .board import build_standard_board
from .enums import CardKind
from .cards import Deck, Card, CaseFile
from .suggestion import Suggestion
from .constants import SUSPECTS

if TYPE_CHECKING:
    from .player import Player

class MessageBus:
    """ Messaging layer for minimal increment, replace w/ Websocket stuff later ig? """
    
    def send_private(self, to_player_id: str, event_type: str, playload: dict) -> None:
        """ TODO: implement via Websocket to sinlge client """
        print("[private]", to_player_id, event_type, playload)

    def broadcast(self, event_type: str, playload: dict) -> None:
        """ TODO: implement via Channels to all players """
        print("[broadcast]", event_type, playload)


class GameManager:
    """ Represents game controller """

    def __init__(self, bus: Optional[MessageBus] = None, lobby_id: Optional[str] = None):

        self.lobby_id: str          # identifier for running game instance
        self.state = GameState()    # authoritative game state controller
        self.deck = Deck()          # deck used to draw case file and deal hands
        self.bus = MessageBus()     # message bus to broadcast events

        # keep track of players' chosen characters
        self._available_characters = set(SUSPECTS)

        # fields for handling disproving
        self._disprove_ring: List[str] = []     # order list of players to prompt
        self._disprove_index: Optional[int] = None  # index ring for current disprover


    def join_lobby(self, player_name: Optional[str]) -> Player:
        """
        Pre: Game not started; capacity < 6; character selection remains 
        Post: Player added to state.players; broadcast lobby update 
        """

        from .player import Player  # local import to avoid circular at module load

        # generate player ID and name
        player_id = str(uuid4())
        base = "Player"
        n = len(self.state.players) + 1
        candidate = f"{base} {n}"       # Player 1, Player 2, etc.
        player_name = candidate

        # create player & add to game state
        p = Player(id = player_id, name = player_name)
        if p.id in self.state.players:
            raise ValueError(f"Player with id {p.id} already exists.")
        self.state.players[p.id] = p

        # broadcast update
        self.bus.broadcast("LobbyUpdated", {
            "players": [
                {"id": pl.id, "name": pl.name, "character": pl.character}
                for pl in self.state.players.values()
            ],
            "count": len(self.state.players),
            "availableCharacters": sorted(self._available_characters),
        })

        # return player
        return p
    

    def choose_character(self, player_id: str, character: str) -> None:     # not in sdd but i figure we need it
        """ 
        Allows user to choose from pool of available characters and 
        removes chosen character from pool. 
        """

        # Enforce “character must exist in the allowed set”.
        if character not in SUSPECTS:
            self.bus.send_private(player_id, "Error", {"message": f"Unknown character: {character}."})
            return

        # check if character is not yet reserverd
        if character not in self._available_characters:
            self.bus.send_private(player_id, "Error", {"message": f"{character} is already taken."})
            return

        # Assign and remove from available pool.
        p = self.state.get_player(player_id)
        p.character = character
        self._available_characters.remove(character)

        # Notify everyone so the UI can gray-out that character.
        self.bus.broadcast("LobbyUpdated", {
            "players": [
                {"id": pl.id, "name": pl.name, "character": pl.character}
                for pl in self.state.players.values()
            ],
            "availableCharacters": sorted(self._available_characters),
        })


    def start_game(self) -> None:
        """
        Builds the board, shuffles deck, draws CaseFile, deals hands, 
        set turn order, broadcast game start event
        """

        # build board layout
        self.state.board = build_standard_board()

        # shuffle deck & draw CaseFile
        self.deck.shuffle()
        cf: CaseFile = self.deck.draw_case_file()
        self.state.solution = cf

        # deal remaining cards evenly among players
        hands: Dict[str, List[Card]] = {pid: [] for pid in self.state.players.keys()}
        self.deck.deal(hands)
        for pid, cards in hands.items():
            self.state.players[pid].hand = cards

        # set turn order and current player
        order = list(self.state.players.keys())
        self.state.turn_order = order
        self.state.current_player_id = order [0] if order else None  # set who starts

        # broadcast Game Started event & private hands
        self.bus.broadcast("GameStarted", self.state.view_for_broadcast())

        # show each player their private hand
        for pid, cards in hands.items():
            self.bus.send_private(pid, "PrivateHand", {
                "hand": [{"id": c.id, "kind": c.kind.name.lower(), "name": c.name} for c in cards]
            })
        
    
    def handle_move(self, player_id: str, target: str) -> None:
        """ Applies move and broadcasts updated game state. """

        # find player and move them
        player = self.state.get_player(player_id)
        self.state.board.move(player, target)

        # broadcast state change
        self.bus.broadcast("stateUpdated", self.state.view_for_broadcast())

    
    def handle_suggestion(self, player_id: str, suspect: str, weapon: str,) -> None:
        """
        Create suggestion w/ player's current room, prompt next player to disprove
        """

        # enforce it's this player's turn
        if self.state.current_player_id and player_id != self.state.current_player_id:
            self.bus.send_private(player_id, "Error", {"message": "Not your turn."})
            return

        # player posistion must be in room
        room_id = self.state.get_player(player_id).position
        if room_id not in self.state.board._room_by_id:
            self.bus.send_private(player_id, "Error", {"message": "You must be in a room to suggest."})
            return

        # build Suggestion object with Card instances
        room_name = self.state.board._room_by_id[room_id].name
        suggestion = Suggestion(
            suggester_id = player_id,
            suspect =Card(CardKind.SUSPECT, suspect, f"SUG-S:{suspect}"),
            weapon  =Card(CardKind.WEAPON, weapon, f"SUG-W{weapon}"),
            room    =Card(CardKind.ROOM, room_name, f"SUG-R:{room_id}"),
            is_accusation = False,
        )
        self.state.pending_suggestion = suggestion

        # iterate through other players to disprove until someone can or wrap back to current player
        order = self.state.turn_order
        i = order.index(player_id)
        self._disprove_ring = order[i + 1:] + order[:i]
        self._disprove_index = 0

        # prompt first candidate
        self._prompt_next_disprover()

    
    def handle_disprove(self, next_player_id: str, card_id: Optional[str]) -> None:
        """ Process disprove attempt of prompted player"""

        suggestion = self.state.pending_suggestion

        # validate active pending suggestion
        if suggestion is None:
            self.bus.send_private(next_player_id, "Error", {"message": "No pending suggestion."})
            return 
        
        # validate this is prompted player
        expected = self._disprove_ring[self._disprove_index]
        if next_player_id != expected:
            self.bus.send_private(next_player_id, "Error", {"message" : "Not your prompt."})
            return
        
        # find cards in hand matching suggestion
        player = self.state.get_player(next_player_id)
        matches = player.can_disprove(self.state.pending_suggestion)

        # if card_id provided, verify it's one of matching cards
        chosen = None
        if card_id:
            chosen = next((c for c in matches if c.id == card_id), None)

        if chosen is not None:
            # match success: show chosen card only to suggester
            self.bus.send_private(suggestion.suggester_id, "PrivateShowCard", {
                "card": {"id": chosen.id, "kind": chosen.kind.name.lower(), "name": chosen.name}
            })
            # broadcast that a card was showm
            self.bus.broadcast("Broadcast", {"message": "A card was shown."})
            # clear suggestion and advance turn
            self._end_turn_after_suggestion()
            return
        
        # no match: advnace to next player
        self._disprove_index += 1

        # prompt next player or advance turn if no players could disprove
        if self._disprove_index >= len(self._disprove_ring):
            self._finish_suggestion_no_disproof()
        else:
            self._prompt_next_disprover()


    def handle_accusation(self, player_id: str, suspect: str, weapon: str, room: str) -> None:
        """ 
        Determines if accusation is correct soultion
        Correct -> declare current player as winner, end game
        Incorrect -> current player is out of the game (can still disprove), p1 turn
        """

        # validate that accuser is current player
        if self.state.current_player_id and player_id != self.state.current_player_id:
            self.bus.send_private(player_id, "Error", {"message": "Not your turn."})
            return
        
        # validate CaseFile exists
        if not self.state.solution:
            self.bus.send_private(player_id, "Error", {"message": "Game has not started."})

        # build accusation as Suggestion object with is_accusatoin = True
        self.state.pending_suggestion = Suggestion(
            suggester_id = player_id,
            suspect =Card(CardKind.SUSPECT, suspect, f"SUG-S:{suspect}"),
            weapon  =Card(CardKind.WEAPON, weapon, f"SUG-W{weapon}"),
            room    =Card(CardKind.ROOM, room, f"SUG-R:{room}"),
            is_accusation = True,
        )

        solution = self.state.solution
        # compute of accusation matches solution
        correct = (
            solution.suspect.name == suspect and
            solution.weapon.name == weapon and
            solution.room.name == room
        )

        # correct accusation: reveal winner and end game
        if correct:
            winner = self.state.get_player(player_id)
            self.bus.broadcast("Game Over", {
                "winner": {
                    "name": winner.name,
                    "character": winner.character
                },
                "solution": {
                    "suspect": solution.suspect.name,
                    "weapon": solution.weapon.name,
                    "room": solution.room.name
                }
            })

            # clear pending suggestion
            self.state.pending_suggestion = None
            return
        
        # incorrect accusation -> player lost
        player = self.state.get_player(player_id)
        player.is_lost = True
        
        # remove player form active turn order
        if player_id in self.state.turn_order:
            self.state.turn_order = [pid for pid in self.state.turn_order if pid != player_id]
    
        # clear pending suggestion
        self.state.pending_suggestion = None

        # broadcast result
        self.bus.broadcast("Broadcast", {
            "message": f"{player.name} made an incorrect accusation and is out"
        })
        self.bus.broadcast("state updated", self.state.view_for_broadcast())

        # if only one player left then they win by default & game over
        active = [pl for pl in self.state.players.values() if not pl.is_lost]
        if len(active) <= 1 and self.state.solution:
            last = active[0] if active else None
            self.bus.broadcast("Game Over", {
                "winner": {
                    "name": last.name if last else None,
                    "character": last.character if last else None
                },
                "solution": {
                    "suspect": self.state.solution.suspect.name,
                    "weapon": self.state.solution.weapon.name,
                    "room": self.state.solution.room.name
                }   
            })
            return
        
        # otherwise, advance to next player
        if self.state.current_player_id == player_id:
            self._advance_turn()
            self.bus.broadcast("TurnAdvanced", {
                "currentPlayer": (
                    {"id": self.state.current_player_id,
                    "name": self.state.players[self.state.current_player_id].name,
                    "character": self.state.players[self.state.current_player_id].character}
                    if self.state.current_player_id else None
                )
            })
        self.bus.broadcast("StateUpdated", self.state.view_for_broadcast())


    # private helper methods

    def _advance_turn(self) -> None:
        """ Rotate current player to next player in turn order. """
        order = self.state.turn_order
        
        cp = self.state.current_player_id
        if cp not in order:
            self.state.current_player_id = order[0]
        
        # find index of current player in turn order
        cp_index = order.index(cp)

        # find and move to next active player (is_lost = False)
        next_id = None
        total_players = len(order)

        for step in range(1, total_players + 1):
            i = (cp_index + step) % total_players
            candidate_id = order[i]
            candidate = self.state.get_player(candidate_id)
            # skip lost players
            if candidate and not getattr(candidate, "is_lost", False):
                next_id = candidate_id
                break

        # update game state
        self.state.current_player_id = next_id

        # broadcast update
        current = self.state.get_player(next_id)
        self.bus.broadcast("Turn Advanced", {
            "current player":{
                "name": current.name,
                "character": current.character,
            }
        })



    def _prompt_next_disprover(self) -> None:
        """Send a private prompt to the next player in the disprove ring."""
        assert self.state.pending_suggestion is not None
        pid = self._disprove_ring[self._disprove_index]
        s = self.state.pending_suggestion
        self.bus.send_private(pid, "PromptDisprove", {
            "suggestion": {
                "suggesterId": s.suggester_id,
                "suspect": s.suspect.name,
                "weapon": s.weapon.name,
                "room": s.room.name,
            }
        })

    def _finish_suggestion_no_disproof(self) -> None:
        """Announce that no one could disprove, then end the turn."""
        self.bus.broadcast("Broadcast", {"message": "No one could disprove."})
        self._end_turn_after_suggestion()

    def _end_turn_after_suggestion(self) -> None:
        """Clear suggestion state and advance to the next player's turn."""
        self.state.pending_suggestion = None
        self._disprove_ring = []
        self._disprove_index = None
        self._advance_turn()
        self.bus.broadcast("TurnAdvanced", {"currentPlayerId": self.state.current_player_id})
        self.bus.broadcast("StateUpdated", self.state.view_for_broadcast())
