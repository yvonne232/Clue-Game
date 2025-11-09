from django.db import models

class Game(models.Model):
    """Represents a single Clue-Less game session."""

    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)

    solution = models.OneToOneField(
        "Solution", on_delete=models.CASCADE, null=True, blank=True
    )

    current_player = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_turn_games",
    )

    def __str__(self):
        status = "Active" if self.is_active else "Finished"
        return f"Game: {self.name} ({status})"
