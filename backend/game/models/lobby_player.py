from django.db import models
import random

class LobbyPlayer(models.Model):
    """Represents a player in the lobby system before a game starts."""
    created_at = models.DateTimeField(auto_now_add=True)
    lobby = models.ForeignKey(
        'Lobby', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='lobby_players'
    )
    character_card = models.ForeignKey(
        'Card',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'card_type': 'CHAR'},
        related_name='lobby_players'
    )

    def __str__(self):
        return f"Player {self.id}"

    class Meta:
        db_table = 'lobby_player'