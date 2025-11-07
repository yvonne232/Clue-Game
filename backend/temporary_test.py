from game.game_engine.board import BoardLayout
# from game.game_engine.movement import can_move, perform_move

board = BoardLayout()
print("Study adjacent to:", board.get_adjacent_rooms("Study"))

# Fake player movement (replace with mock object)
class MockPlayer:
    def __init__(self, room_name):
        self.current_room = type("Room", (), {"name": room_name})()
        self.id = 1
    def save(self):
        print("Mock save called")

player = MockPlayer("Study")

# print("Can move to Kitchen:", can_move(player, "Kitchen"))
# print("Perform move to Kitchen:", perform_move(player, "Kitchen"))