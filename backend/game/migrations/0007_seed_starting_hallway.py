from django.db import migrations


def seed_starting_hallways(apps, schema_editor):
    Card = apps.get_model("game", "Card")
    Hallway = apps.get_model("game", "Hallway")
    Player = apps.get_model("game", "Player")

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
            char = Card.objects.get(name=char_name, card_type="CHAR")
            hallway = Hallway.objects.get(name=hallway_name)
        except (Card.DoesNotExist, Hallway.DoesNotExist):
            continue

        Player.objects.filter(character_card=char).update(
            starting_hallway=hallway,
            current_hallway=hallway,
        )


def clear_starting_hallways(apps, schema_editor):
    Player = apps.get_model("game", "Player")
    Player.objects.update(starting_hallway=None, current_hallway=None)


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0006_game_player"),
    ]

    operations = [
        migrations.RunPython(seed_starting_hallways, clear_starting_hallways),
    ]
    