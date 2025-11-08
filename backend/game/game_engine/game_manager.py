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

        # --- Assign players to starting hallways ---
        suspects = [c.name for c in Card.objects.filter(card_type="CHAR").order_by("id")]
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
        Notifier.broadcast("✅ Game initialized successfully!")

    # ======================================================================
    # Main game loop
    # ======================================================================
    def run_game(self, max_rounds=20):
        Notifier.broadcast("🏁 Starting full game simulation...")
        for round_num in range(1, max_rounds + 1):
            Notifier.broadcast(f"\n===== ROUND {round_num} =====")

            for player in self.players:
                if player["eliminated"]:
                    continue
                self.play_turn(player)

            active = [p for p in self.players if not p["eliminated"]]
            if len(active) == 1:
                Notifier.broadcast(f"🏆 {active[0]['name']} wins by elimination!")
                break

        Notifier.broadcast("\n=== 🏁 Game Over ===")
        Notifier.broadcast(f"🔑 Actual Solution: {self.solution}")

    # ======================================================================
    # Player turn logic
    # ======================================================================
    def play_turn(self, player):
        name = player["name"]
        location = player["location"]
        Notifier.broadcast(f"{name}'s turn ({location})")

        # ---------------- Movement ----------------
        if isinstance(location, Hallway):
            self._move_from_hallway(player)
        elif isinstance(location, Room):
            self._move_from_room(player)
        else:
            Notifier.broadcast(f"⚠️ {name} has invalid location {location}")
            return

        new_loc = player["location"]

        # ---------------- Suggestion ----------------
        if isinstance(new_loc, Room):
            room_name = new_loc.name

            # Choose a suggestion that is not already disproven
            possible_suspects = [
                s for s in [c.name for c in Card.objects.filter(card_type="CHAR")]
                if s not in player["known_cards"]
            ]
            possible_weapons = [
                w for w in [c.name for c in Card.objects.filter(card_type="WEAP")]
                if w not in player["known_cards"]
            ]

            suspect = random.choice(possible_suspects or [c.name for c in Card.objects.filter(card_type="CHAR")])
            weapon = random.choice(possible_weapons or [c.name for c in Card.objects.filter(card_type="WEAP")])

            Notifier.broadcast(f"{name} suggests {suspect} with {weapon} in {room_name}")

            disprove_msg, disproving_card = self.suggestion_engine.handle_suggestion(player, suspect, weapon, room_name)
            Notifier.broadcast(disprove_msg)

            if disproving_card:
                player["known_cards"].add(disproving_card)

            # Occasionally make an accusation
            if random.random() < 0.15:
                guess = {"suspect": suspect, "weapon": weapon, "room": room_name}
                self._make_accusation(player, guess)
        else:
            Notifier.broadcast(f"{name} cannot make a suggestion in a hallway.")

    # ======================================================================
    # Movement functions
    # ======================================================================
    def _move_from_hallway(self, player):
        hallway = player["location"]
        name = player["name"]
        connected_rooms = [hallway.room1, hallway.room2]
        dest = random.choice(connected_rooms)

        hallway.is_occupied = False
        hallway.save(update_fields=["is_occupied"])

        player["location"] = dest
        player["player_obj"].current_room = dest
        player["player_obj"].save(update_fields=["current_room"])
        Notifier.broadcast(f"🚶 {name} moves from {hallway} → {dest}")

    def _move_from_room(self, player):
        room = player["location"]
        name = player["name"]

        # Available unoccupied hallways from this room
        hallways = Hallway.objects.filter(
            models.Q(room1=room) | models.Q(room2=room),
            is_occupied=False
        )
        # Possible secret passage
        secret = None
        if room.has_secret_passage:
            connected = room.connected_rooms.all()
            if connected.exists():
                secret = random.choice(list(connected))

        options = list(hallways)
        if secret:
            options.append(secret)

        if not options:
            Notifier.broadcast(f"🚫 {name} cannot move (no exits available).")
            return

        dest = random.choice(options)
        if isinstance(dest, Hallway):
            dest.is_occupied = True
            dest.save(update_fields=["is_occupied"])
            Notifier.broadcast(f"🚶 {name} moves from {room} → {dest}")
        else:
            Notifier.broadcast(f"✨ {name} takes a secret passage to {dest}")

        player["location"] = dest
        player["player_obj"].current_room = dest if isinstance(dest, Room) else None
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
            raise SystemExit
        else:
            player["eliminated"] = True
            Notifier.broadcast(f"💀 {name} is eliminated for false accusation.")
