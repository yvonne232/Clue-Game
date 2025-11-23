from django.db import models
from django.core.exceptions import ValidationError

class Lobby(models.Model):
    """Represents a game lobby where players can join before starting a game."""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    game_in_progress = models.BooleanField(default=False)

    def clean(self):
        # Check if the lobby has reached maximum capacity
        if self.lobby_players.count() >= 6:
            raise ValidationError("Lobby has reached maximum capacity of 6 players")

    def __str__(self):
        return f"Lobby: {self.name} ({self.lobby_players.count()}/6 players)"

    class Meta:
        verbose_name_plural = "lobbies"