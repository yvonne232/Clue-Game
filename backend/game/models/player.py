from django.db import models
# from django.contrib.auth.models import User   # optional – for real logins


class Player(models.Model):
    """A player in a specific Clue-Less game."""
    game = models.ForeignKey(
        "Game", on_delete=models.CASCADE, related_name="players"
    )

    character_card = models.OneToOneField(
        "Card",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"card_type": "CHAR"},
        help_text="Which character this player represents.",
    )

    starting_position = models.ForeignKey(
        "StartingPosition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players",
        help_text="Static starting position (character ↔ hallway).",
    )

    current_room = models.ForeignKey(
        "Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupants",
        help_text="Room the player currently occupies, if any.",
    )

    current_hallway = models.ForeignKey(
        "Hallway",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupants",
        help_text="Hallway the player currently occupies, if any.",
    )

    is_active_turn = models.BooleanField(default=False)
    is_eliminated = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.character_card.name if self.character_card else f"Player {self.id}"
        return f"{name} ({self.game.name})"

    class Meta:
        unique_together = ("game", "character_card")


class StartingPosition(models.Model):
    character = models.OneToOneField(
        "Card",
        on_delete=models.CASCADE,
        limit_choices_to={"card_type": "CHAR"},
        related_name="starting_position",
    )
    hallway = models.ForeignKey(
        "Hallway",
        on_delete=models.CASCADE,
        related_name="starting_positions",
    )

    def __str__(self):
        return f"{self.character.name} → {self.hallway.name}"
    