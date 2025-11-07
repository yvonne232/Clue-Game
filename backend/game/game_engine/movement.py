"""
Movement rules for Clue-Less:
- From a room → any connected hallway (if not occupied)
- From a hallway → one of its two connected rooms
- Secret passage moves are allowed between corners
"""
from game.models import Room, Hallway, Player
from .board import BoardLayout

board = BoardLayout()

def can_move(player, destination_room_name):
    """Check if the player can move to a destination room."""
    if not player.current_room:
        return False

    current_name = player.current_room.name
    if destination_room_name not in board.get_adjacent_rooms(current_name):
        return False

    # ensure hallway is not occupied if moving into one
    try:
        hallway = Hallway.objects.get(name=destination_room_name)
        if hallway.is_occupied:
            return False
    except Hallway.DoesNotExist:
        pass

    return True


def perform_move(player, destination_room_name):
    """Move the player if valid."""
    if not can_move(player, destination_room_name):
        return False

    new_room = Room.objects.filter(name=destination_room_name).first()
    if new_room:
        player.current_room = new_room
        player.save()
        return True
    return False
