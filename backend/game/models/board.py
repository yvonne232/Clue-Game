# game/models/board.py
from django.db import models

class Room(models.Model):
    """A room on the Clue-Less board (e.g., Kitchen, Study, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    has_secret_passage = models.BooleanField(default=False)
    connected_rooms = models.ManyToManyField('self', symmetrical=False, blank=True)

    def __str__(self):
        return self.name


class Hallway(models.Model):
    """A hallway that connects exactly two rooms."""
    name = models.CharField(max_length=100, unique=True)
    room1 = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='hallway_start'
    )
    room2 = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='hallway_end'
    )
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Hallway between {self.room1.name} and {self.room2.name}"