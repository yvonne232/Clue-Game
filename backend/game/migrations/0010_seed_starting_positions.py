from django.db import migrations


def seed_starting_positions(apps, schema_editor):
    Card = apps.get_model("game", "Card")
    Hallway = apps.get_model("game", "Hallway")
    StartingPosition = apps.get_model("game", "StartingPosition")

    mapping = {
        "Miss Scarlet": "Hallway 2",
        "Colonel Mustard": "Hallway 9",
        "Mrs. White": "Hallway 6",
        "Mr. Green": "Hallway 5",
        "Mrs. Peacock": "Hallway 10",
        "Professor Plum": "Hallway 7",
    }

    for char_name, hallway_name in mapping.items():
        try:
            character = Card.objects.get(name=char_name, card_type="CHAR")
            hallway = Hallway.objects.get(name=hallway_name)
        except (Card.DoesNotExist, Hallway.DoesNotExist):
            continue

        StartingPosition.objects.get_or_create(
            character=character,
            defaults={"hallway": hallway},
        )


def clear_starting_positions(apps, schema_editor):
    StartingPosition = apps.get_model("game", "StartingPosition")
    StartingPosition.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0009_starting_position"),
    ]

    operations = [
        migrations.RunPython(seed_starting_positions, clear_starting_positions),
    ]
from django.db import migrations

def seed_starting_positions(apps, schema_editor):
    Card = apps.get_model("game", "Card")
    Hallway = apps.get_model("game", "Hallway")
    StartingPosition = apps.get_model("game", "StartingPosition")

    mapping = {
        "Miss Scarlet": "Hallway 2",
        "Colonel Mustard": "Hallway 9",
        "Mrs. White": "Hallway 6",
        "Mr. Green": "Hallway 5",
        "Mrs. Peacock": "Hallway 10",
        "Professor Plum": "Hallway 7",
    }

    for char_name, hallway_name in mapping.items():
        try:
            character = Card.objects.get(name=char_name, card_type="CHAR")
            hallway = Hallway.objects.get(name=hallway_name)
        except (Card.DoesNotExist, Hallway.DoesNotExist):
            continue

        StartingPosition.objects.get_or_create(
            character=character,
            defaults={"hallway": hallway},
        )

def clear_starting_positions(apps, schema_editor):
    StartingPosition = apps.get_model("game", "StartingPosition")
    StartingPosition.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ("game", "0009_starting_position"),
    ]

    operations = [
        migrations.RunPython(seed_starting_positions, clear_starting_positions),
    ]