import uuid
import random
from typing import Dict, List, Optional

from django.db import models

from game.game_engine.constants import (
    HALLWAY_DEFINITIONS,
    ROOM_DEFINITIONS,
    STARTING_POSITIONS,
)
from game.game_engine.deck import Deck
from game.game_engine.notifier import Notifier
from game.game_engine.suggestion import SuggestionEngine
from game.game_engine.accusation import AccusationEngine
from game.models import Card, Game, Hallway, Player, Room, StartingPosition


class GameManager:
    """Runtime coordinator for a single interactive Clue-Less game."""

    def __init__(self, game_name: str = "default", lobby_players=None):
        self.room_name = game_name
        self.players: List[Dict] = []
        self.current_index = 0
        self.turn_state = {
            "has_moved": False,
            "made_suggestion": False,
            "has_accused": False,
            "entered_room": False,  # Track if player entered a new room this turn
        }
        self.is_over = False
        self.winner: Optional[str] = None
        self.last_suggestion_result: Optional[Dict] = None
        self.pending_disproof: Dict = {}

        # Ensure we have a database record for the game
        self.game, _ = Game.objects.get_or_create(name=game_name)
        Game.objects.filter(pk=self.game.pk).update(
            is_completed=False,
            is_active=True,
            current_player=None,
        )
        self.game.refresh_from_db()

        # Clear any lingering players from a previous run of the same game
        Player.objects.filter(game=self.game).delete()

        # Build the board layout and starting slots
        self._initialize_board()
        self._initialize_starting_positions()

        # Prepare the deck (creates cards if they do not exist) and mystery solution
        # Delete any existing solution for this game before creating a new one
        if self.game.solution:
            self.game.solution.delete()
        
        self.deck = Deck()
        solution_obj = self.deck.create_solution()
        self.solution = {
            "suspect": solution_obj.character.name,
            "weapon": solution_obj.weapon.name,
            "room": solution_obj.room.name,
        }
        Game.objects.filter(pk=self.game.pk).update(solution=solution_obj)
        self.game.solution = solution_obj
        # Create database-backed players for this session
        self._create_players(lobby_players)

        # Deal cards to players to seed knowledge state
        self._deal_cards()

        # Engines that manage suggestion / accusation side effects
        self.suggestion_engine = SuggestionEngine(self.players, room_name=self.room_name)
        self.accusation_engine = AccusationEngine(self.solution, room_name=self.room_name)

        # Choose the first player (Miss Scarlet goes first if present, otherwise random)
        first_index = None
        for idx, entry in enumerate(self.players):
            if entry["name"] == "Miss Scarlet":
                first_index = idx
                break
        
        # If Miss Scarlet is not in the game, choose a random starting player
        if first_index is None:
            first_index = random.randint(0, len(self.players) - 1)
        
        self._switch_to_player(first_index)
        Notifier.broadcast("✅ Game initialized successfully!", room=self.room_name)

    # ------------------------------------------------------------------
    # Public API used by websocket consumer
    # ------------------------------------------------------------------
    def serialize_state(self) -> Dict:
        current_entry = (
            self.players[self.current_index]
            if self.players and not self.is_over
            else None
        )
        current_payload = (
            {
                "id": current_entry["player_obj"].id,
                "name": current_entry["name"],
            }
            if current_entry
            else None
        )

        return {
            "players": [
                {
                    "id": entry["player_obj"].id,
                    "name": entry["name"],
                    "location": self._format_location(entry["location"]),
                    "location_type": self._location_type(entry["location"]),
                    "eliminated": entry["eliminated"],
                    "arrived_via_suggestion": entry.get("arrived_via_suggestion", False),
                    "hand": sorted(entry.get("hand", [])),  # Original cards dealt to player
                    "known_cards": sorted(entry.get("known_cards", [])),  # All cards known (hand + revealed)
                    "revealed_by": entry.get("revealed_by", {}),  # Dict mapping card_name -> disprover_name
                    "revealed_to": entry.get("revealed_to", {}),  # Dict mapping card_name -> list of player names
                    "possible_solution_cards": self._get_possible_solution_cards(entry),  # Cards that could be in solution
                }
                for entry in self.players
            ],
            "current_player": current_payload,
            "turn_state": dict(self.turn_state),
            "is_active": self.game.is_active,
            "is_completed": self.game.is_completed,
            "is_over": self.is_over,
            "winner": self.winner,
            "last_suggestion": self.last_suggestion_result,
        }

    def _get_possible_solution_cards(self, player_entry: Dict) -> Dict:
        """
        Calculate which cards could still be in the solution from this player's perspective.
        A card is NOT in the solution if:
        - The player has it in their hand
        - The player has seen it revealed by another player
        """
        from game.game_engine.constants import SUSPECTS, WEAPONS, ROOMS
        
        known_cards = set(player_entry.get("known_cards", []))
        
        return {
            "suspects": [s for s in SUSPECTS if s not in known_cards],
            "weapons": [w for w in WEAPONS if w not in known_cards],
            "rooms": [r for r in ROOMS if r not in known_cards],
        }

    def get_player_entry(self, player_id: int) -> Optional[Dict]:
        for entry in self.players:
            if entry["player_obj"].id == player_id:
                return entry
        return None

    def get_current_player(self) -> Optional[Dict]:
        if not self.players:
            return None
        entry = self.players[self.current_index]
        if entry["eliminated"]:
            return None
        return entry

    def get_available_moves(self, player_entry: Dict) -> List[Dict]:
        location = player_entry["location"]
        options: List[Dict] = []

        if isinstance(location, Hallway):
            # Hallways connect two rooms – the player must enter one of them
            for room in (location.room1, location.room2):
                options.append({"name": room.name, "type": "room", "target": room})
        elif isinstance(location, Room):
            # Get all hallways connected to this room
            hallways = Hallway.objects.filter(
                models.Q(room1=location) | models.Q(room2=location),
            ).select_related("room1", "room2")
            
            # Filter out hallways that are occupied by active (non-eliminated) players
            for hallway in hallways:
                # Check if hallway is actually occupied by an active player
                is_occupied_by_active = False
                if hallway.is_occupied:
                    # Check if any active player is in this hallway
                    for entry in self.players:
                        if (not entry["eliminated"] and 
                            isinstance(entry["location"], Hallway) and
                            entry["location"].id == hallway.id):
                            is_occupied_by_active = True
                            break
                
                if not is_occupied_by_active:
                    # Free the hallway if it's marked occupied but no active player is there
                    if hallway.is_occupied:
                        self._set_hallway_occupied(hallway, False)
                    options.append(
                        {"name": hallway.name, "type": "hallway", "target": hallway}
                    )

            # Secret passage (if any)
            for connected_room in location.connected_rooms.all():
                options.append(
                    {
                        "name": connected_room.name,
                        "type": "room",
                        "target": connected_room,
                    }
                )

            # Staying is only an option if the player was dragged into the room by suggestion
            if player_entry.get("arrived_via_suggestion"):
                options.append(
                    {
                        "name": f"Stay in {location.name}",
                        "type": "stay",
                        "target": location,
                    }
                )
        return options

    def move_player(self, player_id: int, destination_name: Optional[str] = None):
        if self.is_over:
            return {"success": False, "error": "The game has already ended."}

        entry = self.get_player_entry(player_id)
        if not entry:
            return {"success": False, "error": "Player not found."}

        current_player = self.get_current_player()
        if current_player is None or current_player is not entry:
            return {"success": False, "error": "It is not this player's turn."}

        if self.turn_state["has_moved"]:
            return {"success": False, "error": "Player has already moved this turn."}

        if entry["eliminated"]:
            return {"success": False, "error": "Eliminated players cannot move."}

        options = self.get_available_moves(entry)
        if not options:
            message = (
                f"🚫 {entry['name']} cannot move and remains in "
                f"{self._format_location(entry['location'])}."
            )
            self.turn_state["has_moved"] = True
            Notifier.broadcast(message, room=self.room_name)
            return {"success": True, "messages": [message]}

        if destination_name is None:
            request_id = str(uuid.uuid4())
            return {
                "success": True,
                "requires_choice": True,
                "options": [opt["name"] for opt in options],
                "player_name": entry["name"],
                "request_id": request_id,
            }

        selected = next(
            (
                opt
                for opt in options
                if opt["name"].lower() == destination_name.lower()
            ),
            None,
        )
        if not selected:
            return {"success": False, "error": "Invalid move destination."}

        self._apply_movement(entry, selected)
        self.turn_state["has_moved"] = True
        # Don't reset arrived_via_suggestion here - it persists until turn ends
        message = f"🚶 {entry['name']} moves to {selected['name']}."
        Notifier.broadcast(message, room=self.room_name)
        return {"success": True, "messages": [message]}

    def make_suggestion_action(self, player_id: int, suspect: str, weapon: str):
        if self.is_over:
            return {"success": False, "error": "The game has already ended."}

        entry = self.get_player_entry(player_id)
        if not entry:
            return {"success": False, "error": "Player not found."}
        if self.get_current_player() is not entry:
            return {"success": False, "error": "It is not this player's turn."}
        if entry["eliminated"]:
            return {"success": False, "error": "Eliminated players cannot act."}

        location = entry["location"]
        if not isinstance(location, Room):
            return {"success": False, "error": "Suggestions may only be made from a room."}

        # Check if player has confirmed their movement
        if not self.turn_state["has_moved"]:
            return {"success": False, "error": "You must confirm your movement before making a suggestion."}

        intro = f"{entry['name']} suggests {suspect} with {weapon} in {location.name}."
        Notifier.broadcast(intro, room=self.room_name)
        
        # Clear any previous suggestion result to avoid stale data
        self.last_suggestion_result = None
        
        # Call handle_suggestion with new return format (dict) of pending disproof state
        disproof_result = self.suggestion_engine.handle_suggestion(
            entry, suspect, weapon, location.name
        )
        
        # Store the pending disproof state for later use
        # include the suggester's database id so we can privately message them
        self.pending_disproof = {
            "suggester_id": entry["player_obj"].id,
            "suggester_name": entry["name"],
            "suspect": suspect,
            "weapon": weapon,
            "room": location.name,
        }
        
        if disproof_result["pending_disproof"]:
            # Disproof pending: disprover must choose a card
            disprover = disproof_result["first_disprover"]
            matching_cards = disproof_result["matching_cards"]
            
            self.pending_disproof["disprover_id"] = disprover["player_obj"].id
            self.pending_disproof["disprover_name"] = disprover["name"]
            self.pending_disproof["matching_cards"] = matching_cards
            
            print(f"[DISPROOF] Waiting for {disprover['name']} to choose from {matching_cards}")
            
            entry["arrived_via_suggestion"] = True
            self.turn_state["made_suggestion"] = True
            
            return {
                "success": True,
                "awaiting_disproof": True,
                "disprover_id": disprover["player_obj"].id,
                "disprover_name": disprover["name"],
                "suggester_name": entry["name"],
                "matching_cards": matching_cards,
                "messages": [intro, disproof_result["message"]],
            }
        else:
            # No one could disprove (message already broadcast by suggestion engine)
            
            self.last_suggestion_result = {
                "suspect": suspect,
                "weapon": weapon,
                "room": location.name,
                "suggester": entry["name"],
                "card": None,
            }
            
            entry["arrived_via_suggestion"] = True
            self.turn_state["made_suggestion"] = True
            
            return {
                "success": True,
                "awaiting_disproof": False,
                "suggester_name": entry["name"],
                "messages": [intro, disproof_result["message"]],
                "payload": dict(self.last_suggestion_result),
            }

    def choose_disproving_card(self, player_id: int, card_name: str):
        """
        Disprover chooses which card to reveal.
        - Validate the card is in their hand and matches the suggestion.
        - Store the revealed card.
        - Return success payload with card name.
        """
        if self.is_over:
            return {"success": False, "error": "The game has already ended."}

        # Check if there's a pending disproof
        if not self.pending_disproof:
            return {"success": False, "error": "No pending disproof."}

        # Verify the player is the disprover
        disprover_id = self.pending_disproof.get("disprover_id")
        if disprover_id != player_id:
            return {"success": False, "error": "You are not the current disprover."}

        # Get the disprover entry
        disprover = self.get_player_entry(player_id)
        if not disprover:
            return {"success": False, "error": "Disprover not found."}

        # Verify the card is in matching cards
        matching_cards = self.pending_disproof.get("matching_cards", [])
        if card_name not in matching_cards:
            return {"success": False, "error": f"Card '{card_name}' is not a valid choice."}

        # Verify the card is in the disprover's hand
        if card_name not in disprover["hand"]:
            return {"success": False, "error": f"Card '{card_name}' is not in your hand."}

        print(f"[DISPROOF] {disprover['name']} chose {card_name} to disprove")

        # Store the revealed card in suggestion result
        suggester_id = self.pending_disproof.get("suggester_id")
        self.last_suggestion_result = {
            "suspect": self.pending_disproof.get("suspect"),
            "weapon": self.pending_disproof.get("weapon"),
            "room": self.pending_disproof.get("room"),
            "suggester": self.pending_disproof.get("suggester_name"),
            "card": card_name,
            "disprover": disprover["name"],
        }

        # Add the revealed card to suggester's known cards
        suggester = self.get_player_entry(suggester_id)
        if suggester:
            suggester["known_cards"].add(card_name)
            # Track who revealed this card to the suggester
            if "revealed_by" not in suggester:
                suggester["revealed_by"] = {}
            suggester["revealed_by"][card_name] = disprover["name"]

        # Track on the disprover's side that they revealed this card to the suggester
        if "revealed_to" not in disprover:
            disprover["revealed_to"] = {}
        if card_name not in disprover["revealed_to"]:
            disprover["revealed_to"][card_name] = []
        if suggester and suggester["name"] not in disprover["revealed_to"][card_name]:
            disprover["revealed_to"][card_name].append(suggester["name"])

        # Broadcast to all players that suggestion was disproved
        Notifier.broadcast(
            f"🃏 {disprover['name']} disproved {self.pending_disproof.get('suggester_name')}'s suggestion.",
            room=self.room_name,
        )

        # Clear pending disproof
        self.pending_disproof = {}

        return {
            "success": True,
            "card": card_name,
            "disprover_name": disprover["name"],
            "suggester_id": suggester_id,
            "suggester_name": self.last_suggestion_result.get("suggester"),
            "messages": [f"{disprover['name']} chose {card_name}."],
        }

    def make_accusation_action(self, player_id: int, suspect: str, weapon: str, room: str):
        if self.is_over:
            return {"success": False, "error": "The game has already ended."}

        entry = self.get_player_entry(player_id)
        if not entry:
            return {"success": False, "error": "Player not found."}
        if self.get_current_player() is not entry:
            return {"success": False, "error": "It is not this player's turn."}
        if entry["eliminated"]:
            return {"success": False, "error": "Eliminated players cannot act."}

        accusation_msg = f"⚖️ {entry['name']} accuses {suspect} with {weapon} in {room}."
        Notifier.broadcast(accusation_msg, room=self.room_name)
        correct = self.accusation_engine.check_accusation(suspect, weapon, room)
        self.turn_state["has_accused"] = True

        if correct:
            self._finalize_game(entry, correct_accusation=True)
            return {
                "success": True,
                "messages": [
                    accusation_msg,
                    f"🏆 {entry['name']} correctly solved the mystery!",
                ],
                "game_over": True,
            }

        entry["eliminated"] = True
        Player.objects.filter(pk=entry["player_obj"].pk).update(is_eliminated=True)
        entry["player_obj"].is_eliminated = True
        
        # Free the hallway if the eliminated player was in one
        location = entry["location"]
        if isinstance(location, Hallway):
            self._set_hallway_occupied(location, False)
        
        Notifier.broadcast(
            f"💀 {entry['name']} is eliminated",
            room=self.room_name,
        )

        remaining = [p for p in self.players if not p["eliminated"]]
        if len(remaining) == 1:
            self._finalize_game(remaining[0], correct_accusation=False)
            return {
                "success": True,
                "messages": [f"{remaining[0]['name']} wins by last player standing!"],
                "game_over": True,
            }

        next_player = self._advance_turn()
        return {
            "success": True,
            "messages": [f"{entry['name']} has been eliminated."],
            "next_player": self.serialize_state()["current_player"],
        }

    def end_turn(self, player_id: int):
        if self.is_over:
            return {"success": False, "error": "The game has already ended."}

        entry = self.get_player_entry(player_id)
        if not entry:
            return {"success": False, "error": "Player not found."}
        if self.get_current_player() is not entry:
            return {"success": False, "error": "It is not this player's turn."}
        if entry["eliminated"]:
            return {"success": False, "error": "Eliminated players cannot act."}

        # Check if player must move first
        if not self.turn_state["has_moved"]:
            moves = self.get_available_moves(entry)
            non_stay_moves = [option for option in moves if option["type"] != "stay"]
            if non_stay_moves:
                return {"success": False, "error": "You must move before ending your turn."}
            # If only "stay" option is available or no moves at all, check if they can stay
            stay_moves = [option for option in moves if option["type"] == "stay"]
            if stay_moves:
                return {"success": False, "error": "You must confirm your movement (stay in room) before ending your turn."}

        # Check if player must make a suggestion
        # Player must make a suggestion if they entered a room this turn
        location = entry["location"]
        if (isinstance(location, Room) and 
            not self.turn_state["made_suggestion"] and 
            self.turn_state["entered_room"]):
            return {"success": False, "error": "You must make a suggestion before ending your turn."}

        next_player = self._advance_turn()
        if not next_player:
            self._finalize_game(None, correct_accusation=False)
            return {
                "success": True,
                "messages": ["No active players remain. Game over."],
                "game_over": True,
            }

        return {
            "success": True,
            "messages": [f"Turn ended. Next up: {next_player['name']}"],
            "next_player": self.serialize_state()["current_player"],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _broadcast(self, message: str):
        Notifier.broadcast(message, room=self.room_name)

    def _finalize_game(self, winner_entry: Optional[Dict], correct_accusation: bool):
        if winner_entry:
            self.winner = winner_entry["name"]
            self._broadcast(f"🏆 {self.winner} wins the game!")
        else:
            self._broadcast("🤷 The game ended without a winner.")
            self.winner = None

        self.is_over = True
        Game.objects.filter(pk=self.game.pk).update(
            is_completed=True,
            is_active=False,
            current_player=None,
        )
        self.game.is_completed = True
        self.game.is_active = False
        self.game.current_player = None

        for entry in self.players:
            if entry["player_obj"].is_active_turn:
                Player.objects.filter(pk=entry["player_obj"].pk).update(is_active_turn=False)
                entry["player_obj"].is_active_turn = False

    def _advance_turn(self) -> Optional[Dict]:
        if not self.players:
            return None

        # Reset arrived_via_suggestion for the current player whose turn is ending
        if self.current_index is not None:
            current_player_entry = self.players[self.current_index]
            current_player_entry["arrived_via_suggestion"] = False

        starting_index = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.players)
            candidate = self.players[self.current_index]
            if not candidate["eliminated"]:
                self._switch_to_player(self.current_index)
                return candidate
            if self.current_index == starting_index:
                return None

    def _switch_to_player(self, index: int):
        self.current_index = index
        current_entry = self.players[self.current_index]

        Game.objects.filter(pk=self.game.pk).update(
            current_player=current_entry["player_obj"]
        )
        self.game.current_player = current_entry["player_obj"]

        for entry in self.players:
            should_be_active = entry is current_entry and not entry["eliminated"]
            if entry["player_obj"].is_active_turn != should_be_active:
                Player.objects.filter(pk=entry["player_obj"].pk).update(
                    is_active_turn=should_be_active
                )
                entry["player_obj"].is_active_turn = should_be_active

        self.turn_state = {
            "has_moved": False,
            "made_suggestion": False,
            "has_accused": False,
            "entered_room": False,  # Track if player entered a new room this turn
        }
        self._broadcast(f"🎯 {current_entry['name']} will act now.")

    def _apply_movement(self, player_entry: Dict, option: Dict):
        current_location = player_entry["location"]
        player_obj = player_entry["player_obj"]

        if isinstance(current_location, Hallway):
            self._set_hallway_occupied(current_location, False)

        option_type = option["type"]
        if option_type == "hallway":
            hallway: Hallway = option["target"]
            if self._is_hallway_occupied(hallway):
                raise ValueError("Hallway became occupied before move could complete.")
            self._set_hallway_occupied(hallway, True)
            player_entry["location"] = hallway
            # Don't reset arrived_via_suggestion here - it persists until turn ends
            Player.objects.filter(pk=player_obj.pk).update(
                current_room=None,
                current_hallway=hallway,
            )
            player_obj.current_room = None
            player_obj.current_hallway = hallway
        elif option_type == "room":
            room: Room = option["target"]
            player_entry["location"] = room
            # Don't reset arrived_via_suggestion here - it persists until turn ends
            self.turn_state["entered_room"] = True  # Player entered a room this turn
            Player.objects.filter(pk=player_obj.pk).update(
                current_room=room,
                current_hallway=None,
            )
            player_obj.current_room = room
            player_obj.current_hallway = None
        elif option_type == "stay":
            # Staying keeps the player in the room but counts as their movement action
            # Player must still make a suggestion since they chose to stay in the room
            # Don't reset arrived_via_suggestion here - it persists until turn ends
            self.turn_state["entered_room"] = True  # Treat "stay" as entering the room for suggestion requirement
        else:
            raise ValueError("Unsupported movement option.")

    def _format_location(self, location) -> Optional[str]:
        if isinstance(location, (Room, Hallway)):
            return location.name
        if location is None:
            return None
        return str(location)

    def _location_type(self, location) -> Optional[str]:
        if isinstance(location, Room):
            return "room"
        if isinstance(location, Hallway):
            return "hallway"
        return None

    def _set_hallway_occupied(self, hallway: Hallway, occupied: bool):
        if hallway is None:
            return
        updated = Hallway.objects.filter(pk=hallway.pk).update(is_occupied=occupied)
        if updated:
            hallway.is_occupied = occupied

    def _is_hallway_occupied(self, hallway: Hallway) -> bool:
        if hallway is None:
            return False
        return Hallway.objects.filter(pk=hallway.pk, is_occupied=True).exists()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _create_players(self, lobby_players):
        if not lobby_players:
            raise RuntimeError("Lobby players required to start the game.")

        for lobby_player in lobby_players:
            if not lobby_player.character_card:
                raise ValueError(
                    f"Player {lobby_player.id} has not selected a character."
                )

            start_pos = StartingPosition.objects.get(
                character=lobby_player.character_card
            )
            hallway = start_pos.hallway
            if self._is_hallway_occupied(hallway):
                raise RuntimeError(
                    f"Starting hallway for {lobby_player.character_card.name} is occupied."
                )

            player = Player.objects.create(
                game=self.game,
                character_name=lobby_player.character_card.name,
                starting_position=start_pos,
                current_hallway=hallway,
                current_room=None,
                is_eliminated=False,
                is_active_turn=False,
            )
            self._set_hallway_occupied(hallway, True)

            self.players.append(
                {
                    "name": lobby_player.character_card.name,
                    "player_obj": player,
                    "location": hallway,
                    "hand": [],
                    "eliminated": False,
                    "known_cards": set(),
                    "revealed_by": {},  # Dict mapping card_name -> disprover_name
                    "revealed_to": {},  # Dict mapping card_name -> list of player names this card was revealed to
                    "arrived_via_suggestion": False,
                }
            )

    def _deal_cards(self):
        hands = self.deck.deal(len(self.players), self.game.solution)
        for index, entry in enumerate(self.players):
            entry["hand"] = hands[index]
            entry["known_cards"] = set(hands[index])
            entry["revealed_by"] = {}  # Reset revealed_by when dealing cards
            entry["revealed_to"] = {}  # Reset revealed_to when dealing cards

    def _initialize_starting_positions(self):
        # If starting positions already exist, assume they are correct
        if StartingPosition.objects.exists():
            return

        character_cards = {
            card.name: card
            for card in Card.objects.filter(card_type="CHAR")
        }

        for name, hallway_code in STARTING_POSITIONS.items():
            card = character_cards.get(name)
            if card is None:
                card, _ = Card.objects.get_or_create(name=name, card_type="CHAR")
            hallway = Hallway.objects.filter(name__startswith=hallway_code).first()
            if hallway:
                StartingPosition.objects.create(character=card, hallway=hallway)

    def _initialize_board(self):
        if Room.objects.count() == len(ROOM_DEFINITIONS) and Hallway.objects.exists():
            return

        Room.objects.all().delete()
        Hallway.objects.all().delete()

        room_index: Dict[str, Room] = {}
        for code, definition in ROOM_DEFINITIONS.items():
            room_index[code] = Room.objects.create(
                name=definition["name"],
                has_secret_passage=bool(definition.get("secret_passage")),
            )

        for code, definition in ROOM_DEFINITIONS.items():
            secret = definition.get("secret_passage")
            if secret:
                room_index[code].connected_rooms.add(room_index[secret])

        for code, definition in HALLWAY_DEFINITIONS.items():
            Hallway.objects.create(
                name=definition["name"],
                room1=room_index[definition["room1"]],
                room2=room_index[definition["room2"]],
                is_occupied=False,
            )
