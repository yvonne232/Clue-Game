from django.db import models
import random

# Create your models here.
class Player(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    isActivePlayer = models.BooleanField(default=False)
    cards = models.TextField()  # Comma-separated list of cards
    position = models.CharField(max_length=100)  # e.g., "Kitchen", "Ballroom"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.name:  # Only set if name is not already set
            self.name = random.choice(['Alice', 'Bob', 'Charlie', 'Diana', 'Egbert', 'Fiona', 'George'])

    def get_cards_list(self):
        return self.cards.split(",") if self.cards else []

    def __str__(self):
        return str(self.id)