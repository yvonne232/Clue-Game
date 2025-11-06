from django.db import models
# from django.contrib.auth.models import User   # optional – for real logins


class Player(models.Model):
    """A player in a specific Clue-Less game."""

    # user = models.ForeignKey(
    #     User, on_delete=models.SET_NULL, null=True, blank=True,
    #     help_text="Linked Django user (optional for authentication)."
    # )

    game = models.ForeignKey(
        'Game', on_delete=models.CASCADE, related_name='players'
    )

    character_card = models.OneToOneField(
        'Card',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'card_type': 'CHAR'},
        help_text="Which character this player represents."
    )

    current_room = models.ForeignKey(
        'Room',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Current room or hallway on the board."
    )

    is_active_turn = models.BooleanField(default=False)
    is_eliminated = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.character_card.name if self.character_card else f"Player {self.id}"
        return f"{name} ({self.game.name})"

    class Meta:
        unique_together = ('game', 'character_card')
