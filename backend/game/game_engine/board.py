# # game/game_engine/board.py
# from game.models import Room, Hallway
# from game.game_engine.notifier import Notifier


# class Board:
#     """Handles all movement and adjacency logic for the Clue-Less board."""

#     def __init__(self):
#         # Preload all rooms and hallways
#         self.rooms = {r.name: r for r in Room.objects.all()}
#         self.hallways = {h.name: h for h in Hallway.objects.all()}

#         if not self.rooms:
#             Notifier.broadcast("⚠️ No Room objects found in the database!")
#         if not self.hallways:
#             Notifier.broadcast("⚠️ No Hallway objects found in the database!")

#     # ----------------------------------------------------------
#     # 🔹 Movement Logic
#     # ----------------------------------------------------------
#     def get_adjacent_rooms(self, room_or_name):
#         """Return all directly connected rooms and hallways for a given room."""
#         if not room_or_name:
#             return []

#         if isinstance(room_or_name, str):
#             room = self.rooms.get(room_or_name)
#         else:
#             room = room_or_name

#         if not room:
#             return []

#         connected = set(room.connected_rooms.all())

#         # Add rooms connected through hallways
#         for h in Hallway.objects.filter(room1=room) | Hallway.objects.filter(room2=room):
#             connected.add(h.room1 if h.room1 != room else h.room2)

#         return list(connected)

#     def get_connected_hallways(self, room):
#         """Return all hallways directly adjacent to the given room."""
#         if not room:
#             return []
#         hallways = []
#         for h in Hallway.objects.all():
#             if h.room1 == room or h.room2 == room:
#                 hallways.append(h)
#         return hallways

#     # ----------------------------------------------------------
#     # 🔹 Secret Passage
#     # ----------------------------------------------------------
#     def get_secret_passage(self, room_name):
#         """Return the room name that’s diagonally connected via secret passage."""
#         secret_pairs = {
#             "Study": "Kitchen",
#             "Kitchen": "Study",
#             "Conservatory": "Lounge",
#             "Lounge": "Conservatory",
#         }
#         return self.rooms.get(secret_pairs.get(room_name))

#     # ----------------------------------------------------------
#     # 🔹 Hallway Utilities
#     # ----------------------------------------------------------
#     def get_hallway_between(self, room1, room2):
#         """Return the hallway object connecting two rooms, if any."""
#         return Hallway.objects.filter(
#             room1__in=[room1, room2], room2__in=[room1, room2]
#         ).first()

#     def is_hallway_occupied(self, hallway_name):
#         """Check if hallway is currently occupied."""
#         h = self.hallways.get(hallway_name)
#         return h.is_occupied if h else False

#     def set_hallway_occupancy(self, hallway_name, occupied=True):
#         """Mark a hallway as occupied or free."""
#         h = self.hallways.get(hallway_name)
#         if h:
#             h.is_occupied = occupied
#             h.save(update_fields=["is_occupied"])

#     # ----------------------------------------------------------
#     # 🔹 Summary Helpers
#     # ----------------------------------------------------------
#     def describe(self):
#         """Print out board layout for debugging."""
#         Notifier.broadcast("🗺️ Board Layout:")
#         for r in Room.objects.all():
#             connected = ", ".join([x.name for x in r.connected_rooms.all()])
#             hallways = ", ".join([h.name for h in self.get_connected_hallways(r)])
#             Notifier.broadcast(f"{r.name} → Rooms: [{connected}] | Hallways: [{hallways}]")
