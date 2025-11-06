from django.db import models

class Card(models.Model):
    """Represents one of the 21 Clue-Less cards."""
    CARD_TYPES = [
        ('CHAR', 'Character'),
        ('WEAP', 'Weapon'),
        ('ROOM', 'Room'),
    ]

    name = models.CharField(max_length=100, unique=True)
    card_type = models.CharField(max_length=5, choices=CARD_TYPES)

    def __str__(self):
        return f"{self.name} ({self.get_card_type_display()})"


class Solution(models.Model):
    """Represents the mystery combination of one character, one weapon, and one room."""
    character = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='solution_character',
        limit_choices_to={'card_type': 'CHAR'},
    )
    weapon = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='solution_weapon',
        limit_choices_to={'card_type': 'WEAP'},
    )
    room = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name='solution_room',
        limit_choices_to={'card_type': 'ROOM'},
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solution: {self.character.name}, {self.weapon.name}, {self.room.name}"
