import random
from django.db import models
from game.models import Game, Player, Card, Room, Hallway
from game.game_engine.deck import Deck
from game.game_engine.suggestion import SuggestionEngine
from game.game_engine.accusation import AccusationEngine
from game.game_engine.notifier import Notifier


class GameManager:
    """
    Coordinates a full Clue-Less game round using real database data.
    Each Player corresponds to a DB record and moves logically across the board.
    """

    def __init__(self, game_name="default"):
        Notifier.broadcast(f"🎲 Loading game '{game_name}' from database...")

        # --- Load or create the game ---
        self.game, _ = Game.objects.get_or_create(name=game_name)
        self.game.is_completed = False
        self.game.is_active = True
        self.game.current_player = None
        self.game.save(update_fields=["is_completed", "is_active", "current_player"])

        # --- Clear old players for a clean simulation ---
        Player.objects.filter(game=self.game).delete()

        # --- Initialize Deck (from real DB cards) ---
        self.deck = Deck()
        self.solution = self.deck.create_solution()
        Notifier.broadcast(f"Secret solution set: {self.solution}")

        # --- Load Rooms and Hallways ---
        self.rooms = list(Room.objects.all())
        self.hallways = list(Hallway.objects.all())
        if not self.rooms or not self.hallways:
            raise RuntimeError("❌ Missing Room or Hallway objects — run migrations first.")

        # --- Cache card names ---
        self.character_names = [
            c.name for c in Card.objects.filter(card_type="CHAR").order_by("id")
        ]
        self.weapon_names = [
            w.name for w in Card.objects.filter(card_type="WEAP").order_by("id")
        ]

        # --- Clear hallway occupancy first ---
        for hw in Hallway.objects.all():
            hw.is_occupied = False
            hw.save(update_fields=["is_occupied"])

        # --- Assign players to canonical starting hallways (based on DB names) ---
        starting_positions = {
            "Miss Scarlet": "Hallway 2",      # Hall – Lounge
            "Colonel Mustard": "Hallway 9",   # Lounge – Dining Room
            "Mrs. White": "Hallway 6",        # Ballroom – Kitchen
            "Mr. Green": "Hallway 5",         # Conservatory – Ballroom
            "Mrs. Peacock": "Hallway 10",     # Library – Conservatory
            "Professor Plum": "Hallway 7",    # Study – Library
        }

        self.players = []
        for name, hallway_name in starting_positions.items():
            char_card = Card.objects.get(name=name)
            hallway = Hallway.objects.filter(name=hallway_name).first()
            if not hallway:
                raise RuntimeError(f"Missing hallway: {hallway_name} (check migration data)")

            # Create player and set position
            player = Player.objects.create(
                game=self.game,
                character_card=char_card,
                current_room=None,
                is_eliminated=False,
            )

            # Update hallway occupancy
            hallway.is_occupied = True
            hallway.save(update_fields=["is_occupied"])

            # Register in memory
            self.players.append({
                "name": name,
                "player_obj": player,
                "location": hallway,
                "hand": [],
                "eliminated": False,
                "known_cards": set(),
                "arrived_via_suggestion": False,
            })

        # --- Deal cards ---
        hands = self.deck.deal(len(self.players))
        for i, p in enumerate(self.players):
            p["hand"] = hands[i]
            p["known_cards"].update(hands[i])

        # --- Announce hands (for debug only) ---
        Notifier.broadcast("\n --- Player Hands ---")
        for p in self.players:
            Notifier.broadcast(f"{p['name']}: {', '.join(p['hand'])}")
        Notifier.broadcast("------------------------")

        # --- Engines ---
        self.suggestion_engine = SuggestionEngine(self.players)
        self.accusation_engine = AccusationEngine(self.solution)
        self.is_over = False
        self.winner = None
        self.rounds_played = 0

        Notifier.broadcast("✅ Game initialized successfully!")

    # ======================================================================
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

        hallway.is_occupied = False
        hallway.save(update_fields=["is_occupied"])

        dest = random.choice(connected_rooms)
        player["location"] = dest
        player["player_obj"].current_room = dest
        player["player_obj"].save(update_fields=["current_room"])
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
            dest.is_occupied = True
            dest.save(update_fields=["is_occupied"])
            player["location"] = dest
            player["player_obj"].current_room = None
            Notifier.broadcast(f"🚶 {name} moves from {room.name} → {dest.name}")
        else:
            player["location"] = dest
            player["player_obj"].current_room = dest
            Notifier.broadcast(
                f"✨ {name} takes a secret passage from {room.name} → {dest.name}"
            )

        player["player_obj"].save(update_fields=["current_room"])

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
            self.game.is_completed = True
            self.game.is_active = False
            self.game.save(update_fields=["is_completed", "is_active"])
        else:
            player["eliminated"] = True
            player["player_obj"].is_eliminated = True
            player["player_obj"].save(update_fields=["is_eliminated"])
            Notifier.broadcast(f"💀 {name} is eliminated for false accusation.")
