from django.db import migrations


def seed_players(apps, schema_editor):
    Game = apps.get_model("game", "Game")
    Player = apps.get_model("game", "Player")
    Card = apps.get_model("game", "Card")
    StartingPosition = apps.get_model("game", "StartingPosition")

    game, _ = Game.objects.get_or_create(name="default")

    # Clean out any stale rows
    Player.objects.filter(game=game).delete()

    mapping = [
        "Miss Scarlet",
        "Colonel Mustard",
        "Mrs. White",
        "Mr. Green",
        "Mrs. Peacock",
        "Professor Plum",
    ]

    for char_name in mapping:
        try:
            character = Card.objects.get(name=char_name, card_type="CHAR")
            start_pos = StartingPosition.objects.get(character=character)
        except (Card.DoesNotExist, StartingPosition.DoesNotExist):
            continue

        Player.objects.create(
            game=game,
            character_card=character,
            starting_position=start_pos,
            current_hallway=start_pos.hallway,
            current_room=None,
            is_eliminated=False,
            is_active_turn=False,
        )


def clear_players(apps, schema_editor):
    Player = apps.get_model("game", "Player")
    Player.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0010_seed_starting_positions"),
    ]

    operations = [
        migrations.RunPython(seed_players, clear_players),
    ]