import random
from django.db import models
from game.models import Game, Player, Card, Room, Hallway, StartingPosition
from game.game_engine.deck import Deck
from game.game_engine.suggestion import SuggestionEngine
from game.game_engine.accusation import AccusationEngine
from game.game_engine.notifier import Notifier


class GameManager:
    """
    Coordinates a full Clue-Less game round using real database data.
    Each Player corresponds to a DB record and moves logically across the board.
    """

    def __init__(self, game_name="default", lobby_players=None):
        try:
            Notifier.broadcast(f"🎲 Loading game '{game_name}' from database...")

            # --- Load or create the game ---
            self.game, _ = Game.objects.get_or_create(name=game_name)
            Game.objects.filter(pk=self.game.pk).update(
                is_completed=False,
                is_active=True,
                current_player=None,
            )
            self.game.is_completed = False
            self.game.is_active = True
            self.game.current_player = None

            # --- Clear old players for a clean simulation ---
            Player.objects.filter(game=self.game).delete()
            
            # --- Clean up any orphaned character cards ---
            # Get all character cards currently in use by lobby players
            used_character_cards = Card.objects.filter(
                lobby_players__isnull=False
            ).distinct()
            
            # Delete character cards that aren't used in any lobby
            Card.objects.filter(
                card_type='CHAR'
            ).exclude(
                id__in=used_character_cards.values('id')
            ).delete()

            # --- Initialize Deck ---
            # This will ensure all cards exist and are properly loaded
            self.deck = Deck()

            solution_obj = self.deck.create_solution()
            self.solution = {
                "suspect": solution_obj.character.name,
                "weapon": solution_obj.weapon.name,
                "room": solution_obj.room.name,
            }
            Game.objects.filter(pk=self.game.pk).update(solution=solution_obj)
            self.game.solution = solution_obj
        
            Notifier.broadcast(f"Secret solution set: {self.solution}")

            # --- Load Rooms and Hallways ---
            self._initialize_board()
            self.rooms = list(Room.objects.all())
            self.hallways = list(Hallway.objects.all())
            if not self.rooms or not self.hallways:
                raise RuntimeError("❌ Missing Room or Hallway objects — run migrations first.")

            # --- Initialize Starting Positions ---
            self._initialize_starting_positions()

            # --- Cache card names ---
            self.character_names = [
                c.name for c in Card.objects.filter(card_type="CHAR").order_by("id")
            ]
            self.weapon_names = [
                w.name for w in Card.objects.filter(card_type="WEAP").order_by("id")
            ]

            self.players = []

            if lobby_players:
                # Use the provided lobby players to set up the game
                for lobby_player in lobby_players:
                    if not lobby_player.character_card:
                        raise ValueError(f"Player {lobby_player.id} has not selected a character")
                    
                    # Find starting position for this character
                    try:
                        start_pos = StartingPosition.objects.get(
                            character=lobby_player.character_card
                        )
                    except StartingPosition.DoesNotExist:
                        raise RuntimeError(f"No starting position found for character {lobby_player.character_card.name}")

                    hallway = start_pos.hallway
                    if self._is_hallway_occupied(hallway):
                        raise RuntimeError(f"Starting hallway for {lobby_player.character_card.name} is already occupied")

                    # Create a game player with a copy of the character card
                    character_card, _ = Card.objects.get_or_create(
                        name=lobby_player.character_card.name,
                        card_type='CHAR'
                    )
                    
                    # Create game player
                    player = Player.objects.create(
                        game=self.game,
                        character_card=character_card,  # Use the new card instance
                        starting_position=start_pos,
                        current_hallway=hallway,
                        current_room=None,
                        is_eliminated=False,
                        is_active_turn=False,
                    )
                    self._set_hallway_occupied(hallway, True)

                    # Register in memory
                    self.players.append({
                        "name": lobby_player.character_card.name,
                        "player_obj": player,
                        "location": hallway,
                        "hand": [],
                        "eliminated": False,
                        "known_cards": set(),
                        "arrived_via_suggestion": False,
                    })
            else:
                # Use all available starting positions (old behavior)
                positions = list(
                    StartingPosition.objects.select_related("hallway", "character")
                )
                if not positions:
                    raise RuntimeError(
                        "❌ No starting positions available. Seed them via migrations or admin."
                    )

                for pos in positions:
                    hallway = pos.hallway
                    character = pos.character
                    if hallway is None or character is None:
                        Notifier.broadcast(f"⚠️ Skipping starting position with missing data: {pos}")
                        continue

                    player = Player.objects.create(
                        game=self.game,
                        character_card=character,
                        starting_position=pos,
                        current_hallway=pos.hallway,
                        current_room=None,
                        is_eliminated=False,
                        is_active_turn=False,
                    )
                    self._set_hallway_occupied(hallway, True)

                    # Register in memory
                    self.players.append(
                        {
                            "name": character.name,
                            "player_obj": player,
                            "location": hallway,
                            "hand": [],
                            "eliminated": False,
                            "known_cards": set(),
                            "arrived_via_suggestion": False,
                        }
                    )

            # --- Deal cards ---
            if not self.players:
                raise RuntimeError(
                    "❌ No players available. Ensure StartingPosition rows exist before starting the game."
                )

            hands = self.deck.deal(len(self.players))
            for i, p in enumerate(self.players):
                p["hand"] = hands[i]
                p["known_cards"].update(hands[i])

            # --- Announce hands (for debug only) ---
            Notifier.broadcast("\n --- Player Hands ---")
            for p in self.players:
                Notifier.broadcast(f"{p['name']}: {', '.join(p['hand'])}")
            Notifier.broadcast("------------------------")

            # --- Initialize game engines ---
            self.suggestion_engine = SuggestionEngine(self.players)
            self.accusation_engine = AccusationEngine(self.solution)
            self.is_over = False
            self.winner = None
            self.rounds_played = 0

            Notifier.broadcast("✅ Game initialized successfully!")
            
        except Exception as e:
            Notifier.broadcast(f"❌ Failed to initialize game: {str(e)}")
            # Roll back any partial initialization
            if hasattr(self, 'game') and self.game:
                Game.objects.filter(pk=self.game.pk).delete()
            raise    # ======================================================================
    # Main game loop
    # ======================================================================
    def run_game(self, max_rounds=20):
        Notifier.broadcast("🏁 Starting full game simulation...")
        self.rounds_played = 0

        for round_num in range(1, max_rounds + 1):
            Notifier.broadcast(f"\n===== ROUND {round_num} =====")

            for player in self.players:
                if player["eliminated"]:
                    continue
                player_obj = player["player_obj"]
                Game.objects.filter(pk=self.game.pk).update(current_player=player_obj)
                self.game.current_player = player_obj
                self.play_turn(player)
                if self.is_over:
                    break

            self.rounds_played = round_num
            if self.is_over:
                break

            active = [p for p in self.players if not p["eliminated"]]
            if len(active) == 1:
                self.winner = active[0]["name"]
                self.is_over = True
                Notifier.broadcast(f"🏆 {self.winner} wins by elimination!")
                break

        Notifier.broadcast("\n=== 🏁 Game Over ===")
        Notifier.broadcast(f"🔑 Actual Solution: {self.solution}")

        # Update game state before returning
        Game.objects.filter(pk=self.game.pk).update(current_player=None)
        self.game.current_player = None

        return {
            "game": self.game.name,
            "rounds_played": self.rounds_played,
            "winner": self.winner,
            "solution": self.solution,
            "players": [
                {
                    "name": p["name"],
                    "location": self._format_location(p["location"]),
                    "eliminated": p["eliminated"],
                    "cards_in_hand": len(p["hand"]),
                }
                for p in self.players
            ],
        }

    # ======================================================================
    # Player turn logic
    # ======================================================================
    def play_turn(self, player):
        name = player["name"]
        location = player["location"]
        Notifier.broadcast(f"{name}'s turn ({self._format_location(location)})")

        if isinstance(location, Hallway):
            self._move_from_hallway(player)
        elif isinstance(location, Room):
            self._move_from_room(player, player.get("arrived_via_suggestion", False))
        else:
            Notifier.broadcast(f"⚠️ {name} has invalid location {location}")
            return

        player["arrived_via_suggestion"] = False
        new_loc = player["location"]

        if isinstance(new_loc, Room):
            room_name = new_loc.name

            possible_suspects = [
                s for s in self.character_names if s not in player["known_cards"]
            ] or self.character_names
            possible_weapons = [
                w for w in self.weapon_names if w not in player["known_cards"]
            ] or self.weapon_names

            suspect = random.choice(possible_suspects)
            weapon = random.choice(possible_weapons)

            Notifier.broadcast(f"{name} suggests {suspect} with {weapon} in {room_name}")

            disprove_msg, disproving_card = self.suggestion_engine.handle_suggestion(player, suspect, weapon, room_name)
            Notifier.broadcast(disprove_msg)

            if disproving_card:
                player["known_cards"].add(disproving_card)

            # Occasionally make an accusation
            if not self.is_over and random.random() < 0.15:
                guess = {"suspect": suspect, "weapon": weapon, "room": room_name}
                self._make_accusation(player, guess)
        else:
            Notifier.broadcast(f"{name} cannot make a suggestion in a hallway.")

    # ======================================================================
    # Movement functions
    # ======================================================================
    def _format_location(self, location):
        if isinstance(location, Room):
            return location.name
        if isinstance(location, Hallway):
            return location.name
        return str(location)

    def _move_from_hallway(self, player):
        hallway = player["location"]
        name = player["name"]
        connected_rooms = [hallway.room1, hallway.room2]

        self._set_hallway_occupied(hallway, False)

        dest = random.choice(connected_rooms)
        player["location"] = dest
        player_obj = player["player_obj"]
        Player.objects.filter(pk=player_obj.pk).update(
            current_hallway=None,
            current_room=dest,
        )
        player_obj.current_hallway = None
        player_obj.current_room = dest
        Notifier.broadcast(f"🚶 {name} moves from {hallway.name} → {dest.name}")

    def _move_from_room(self, player, can_stay):
        room = player["location"]
        name = player["name"]

        hallways = list(
            Hallway.objects.filter(
                models.Q(room1=room) | models.Q(room2=room), is_occupied=False
            )
        )

        secret_room = None
        if room.has_secret_passage:
            connected = list(room.connected_rooms.all())
            if connected:
                secret_room = random.choice(connected)

        if can_stay:
            if (not hallways and not secret_room) or random.choice([True, False]):
                Notifier.broadcast(
                    f"🛑 {name} stays in {room.name} after being pulled in by a suggestion."
                )
                return

        options = hallways[:]
        if secret_room:
            options.append(secret_room)

        if not options:
            Notifier.broadcast(
                f"🚫 {name} cannot move (all exits blocked) and remains in {room.name}."
            )
            return

        dest = random.choice(options)
        if isinstance(dest, Hallway):
            self._set_hallway_occupied(dest, True)
            player["location"] = dest
            player_obj = player["player_obj"]
            Player.objects.filter(pk=player_obj.pk).update(
                current_room=None,
                current_hallway=dest,
            )
            player_obj.current_room = None
            player_obj.current_hallway = dest
            Notifier.broadcast(f"🚶 {name} moves from {room.name} → {dest.name}")
        else:
            player["location"] = dest
            player_obj = player["player_obj"]
            Player.objects.filter(pk=player_obj.pk).update(
                current_room=dest,
                current_hallway=None,
            )
            player_obj.current_room = dest
            player_obj.current_hallway = None
            Notifier.broadcast(
                f"✨ {name} takes a secret passage from {room.name} → {dest.name}"
            )

    # ======================================================================
    # Accusation phase
    # ======================================================================
    def _make_accusation(self, player, guess):
        name = player["name"]
        Notifier.broadcast(f"⚖️ {name} makes an accusation: {guess}")
        correct = self.accusation_engine.check_accusation(**guess)
        if correct:
            Notifier.broadcast(f"🏆 {name} correctly solved the mystery!")
            self.winner = name
            self.is_over = True
            Game.objects.filter(pk=self.game.pk).update(
                is_completed=True,
                is_active=False,
            )
            self.game.is_completed = True
            self.game.is_active = False
        else:
            player["eliminated"] = True
            Player.objects.filter(pk=player["player_obj"].pk).update(is_eliminated=True)
            player["player_obj"].is_eliminated = True
            Notifier.broadcast(f"💀 {name} is eliminated for false accusation.")

    # ======================================================================
    # Helper utilities
    # ======================================================================
    def _get_starting_positions(self):
        return list(
            StartingPosition.objects.select_related("hallway", "character")
        )

    def _set_hallway_occupied(self, hallway, occupied):
        if hallway is None:
            return
        updated = Hallway.objects.filter(pk=hallway.pk).update(is_occupied=occupied)
        if updated:
            hallway.is_occupied = occupied

    def _is_hallway_occupied(self, hallway):
        if hallway is None:
            return False
        return Hallway.objects.get(pk=hallway.pk).is_occupied

    def _initialize_starting_positions(self):
        """Initialize the starting positions for each character."""
        # Clear existing starting positions
        StartingPosition.objects.all().delete()

        # Map of character names to their starting hallways and hallway IDs
        character_starts = {
            "Miss Scarlet": ("H11", "Between Lounge and Hall"),
            "Colonel Mustard": ("H08", "Between Dining Room and Lounge"),
            "Professor Plum": ("H10", "Between Library and Study"),
            "Mrs. Peacock": ("H05", "Between Conservatory and Library"),
            "Mr. Green": ("H02", "Between Ballroom and Conservatory"),
            "Mrs. White": ("H01", "Between Kitchen and Ballroom")
        }

        # Get all character cards
        character_cards = Card.objects.filter(card_type="CHAR")
        
        Notifier.broadcast("🎮 Setting up starting positions...")
        
        # Create starting positions for each character
        success_count = 0
        for card in character_cards:
            if card.name in character_starts:
                hallway_id, _ = character_starts[card.name]
                try:
                    # First try to find by ID (which we use internally)
                    hallway = Hallway.objects.get(name__startswith=hallway_id)
                    StartingPosition.objects.create(
                        character=card,
                        hallway=hallway
                    )
                    success_count += 1
                except Hallway.DoesNotExist:
                    Notifier.broadcast(f"❌ Could not find hallway {hallway_id} for {card.name}")
        
        Notifier.broadcast(f"✅ Successfully set up {success_count} starting positions")

    def _initialize_board(self):
        """Initialize the game board with standard rooms and hallways."""
        # Clear existing rooms and hallways
        Room.objects.all().delete()
        Hallway.objects.all().delete()

        # Create rooms
        room_data = {
            "R00": ("Kitchen", ["H01", "H03"], "R22"),
            "R01": ("Ballroom", ["H01", "H02", "H04"], None),
            "R02": ("Conservatory", ["H02", "H05"], "R20"),
            "R10": ("Dining Room", ["H03", "H06", "H08"], None),
            "R11": ("Billiard Room", ["H04", "H06", "H07", "H09"], None),
            "R12": ("Library", ["H05", "H07", "H10"], None),
            "R20": ("Lounge", ["H08", "H11"], "R02"),
            "R21": ("Hall", ["H09", "H11", "H12"], None),
            "R22": ("Study", ["H10", "H12"], "R00")
        }

        room_objects = {}
        for room_id, (name, connected_halls, secret_to) in room_data.items():
            room = Room.objects.create(
                name=name,
                has_secret_passage=bool(secret_to)
            )
            room_objects[room_id] = room

        # Set up secret passages
        for room_id, (_, _, secret_to) in room_data.items():
            if secret_to:
                room = room_objects[room_id]
                room.connected_rooms.add(room_objects[secret_to])

        # Create hallways
        hallway_data = {
            "H01": ("H01 - Between Kitchen and Ballroom", "R00", "R01"),
            "H02": ("H02 - Between Ballroom and Conservatory", "R01", "R02"),
            "H03": ("H03 - Between Kitchen and Dining Room", "R00", "R10"),
            "H04": ("H04 - Between Ballroom and Billiard Room", "R01", "R11"),
            "H05": ("H05 - Between Conservatory and Library", "R02", "R12"),
            "H06": ("H06 - Between Dining Room and Billiard Room", "R10", "R11"),
            "H07": ("H07 - Between Billiard Room and Library", "R11", "R12"),
            "H08": ("H08 - Between Dining Room and Lounge", "R10", "R20"),
            "H09": ("H09 - Between Billiard Room and Hall", "R11", "R21"),
            "H10": ("H10 - Between Library and Study", "R12", "R22"),
            "H11": ("H11 - Between Lounge and Hall", "R20", "R21"),
            "H12": ("H12 - Between Hall and Study", "R21", "R22")
        }

        for hall_id, (name, room1_id, room2_id) in hallway_data.items():
            Hallway.objects.create(
                name=name,
                room1=room_objects[room1_id],
                room2=room_objects[room2_id],
                is_occupied=False
            )
