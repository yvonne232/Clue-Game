import random
from game.models import Player, Room, Hallway
from game.game_engine.notifier import Notifier


class SuggestionEngine:
    """
    Handles suggestion logic: move the suspect, find who can disprove, and report results.
    """

    def __init__(self, players):
        self.players = players  # list of dicts from GameManager

    # ======================================================================
    # Core logic
    # ======================================================================
    def handle_suggestion(self, suggesting_player, suspect, weapon, room_name):
        """
        Process a suggestion:
        - Move the suspect to the suggested room.
        - Iterate through other players to find who can disprove.
        - Return (message, disproving_card or None)
        """

        suggester_name = suggesting_player["name"]

        # Move the suspect to the suggested room
        suspect_player = next((p for p in self.players if p["name"] == suspect), None)
        if suspect_player and suspect_player is not suggesting_player:
            try:
                new_room = Room.objects.get(name=room_name)
            except Room.DoesNotExist:
                return (f"⚠️ Room {room_name} not found.", None)

            previous_location = suspect_player["location"]
            if isinstance(previous_location, Hallway):
                updated = Hallway.objects.filter(pk=previous_location.pk).update(is_occupied=False)
                if updated:
                    previous_location.is_occupied = False

            suspect_player["location"] = new_room
            player_obj = suspect_player["player_obj"]
            Player.objects.filter(pk=player_obj.pk).update(
                current_hallway=None,
                current_room=new_room,
            )
            player_obj.current_hallway = None
            player_obj.current_room = new_room
            suspect_player["arrived_via_suggestion"] = True
            Notifier.broadcast(f"  {suspect} was moved to {room_name} due to the suggestion.")
        elif suspect_player:
            Notifier.broadcast(f"  {suspect} is already in {room_name}.")

        # Find players in order (excluding the suggester)
        player_order = self._rotate_players(suggesting_player)

        # Check each for disproof
        for p in player_order:
            if p["eliminated"]:
                continue
            matching_cards = [
                card for card in p["hand"]
                if card in {suspect, weapon, room_name}
            ]
            if matching_cards:
                chosen_card = random.choice(matching_cards)
                Notifier.broadcast(f"🃏 {p['name']} disproved using {chosen_card}.")
                return (f"{p['name']} disproved {suggester_name}'s suggestion.", chosen_card)

        # 4️⃣ No one can disprove
        Notifier.broadcast(f"❌ No one could disprove {suggester_name}'s suggestion!")
        return (f"No one could disprove {suggester_name}'s suggestion.", None)

    # ======================================================================
    # Helper: rotate player order
    # ======================================================================
    def _rotate_players(self, current_player):
        """Return players in clockwise order starting after the current one."""
        idx = self.players.index(current_player)
        rotated = self.players[idx + 1 :] + self.players[:idx]
        return rotated
