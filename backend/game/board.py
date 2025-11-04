# board.py
# Purpose: Maintains the board state pertinent to the location of the players

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Set
from .player import Player

LocationId = str        # unique string ID for room or hallway
PlayerId = str          # player ID

@dataclass(frozen=True) # constant layout (ummutable)
class Room:
    """ Represents one of nine rooms on the board. """
    id: LocationId      # unique identifier for this room
    name: str           # display name
    doors: list[LocationId] = field(default_factory=list)   # connected hallways (immutable)
    secret_passage_to: Optional[LocationId] = None          # optional room ID accessed via secret passage

@dataclass(eq=False, unsafe_hash=True)
class Hallway:
    """ Represents a hallway on board. Connects two rooms. """
    id: LocationId      # unique identifier for this hallway
    name: str           # display name
    between: Tuple[LocationId, LocationId]  # the two rooms it connects
    occupied_by: Optional[PlayerId] = None  # player currently in hallway (none if empty)


class Board:
    """ 
    Represents 3x3 game board: contains all Rooms and Hallways. 
    Provides methods to validate and apply player movements.
    """
    def __init__(self, rooms: Set[Room], hallways: Set[Hallway]):
        """ Initialize board. """

        self.rooms:     Set[Room] = rooms           # 9 room objects
        self.hallways:  Set[Hallway] = hallways     # 12 hallway objects


        self._room_by_id: Dict[LocationId, Room] = {r.id: r for r in rooms}
        self._hallway_by_id: Dict[LocationId, Hallway] = {h.id: h for h in hallways}

    def is_move_legal(self, from_id: Optional[LocationId], to_id: LocationId) -> bool:
        """ Ensures adjacency, hallway availability, secret passage rules, hallway occupancy. """

        if from_id is None:     # guard: invalid source (if player trie to move before being placed on board)
            return False
        
        # determine source/target (room or hallway) by IDs
        from_room       = from_id in self._room_by_id
        to_room         = to_id in self._room_by_id
        from_hallway    = from_id in self._hallway_by_id
        to_hallway      = to_id in self._hallway_by_id

        # room -> room (secret passage)
        if from_room and to_room:
            return self._room_by_id[from_id].secret_passage_to == to_id
        
        # room -> hallway (hallway must connected to room door and be unoccupied)
        if from_room and to_hallway:
            return (to_id in self._room_by_id[from_id].doors
                    and self._hallway_by_id[to_id].occupied_by is None)
        
        # hallway -> room (must be a room connected to hallway)
        if from_hallway and to_room:
            r1, r2 = self._hallway_by_id[from_id].between
            return to_id in (r1, r2)
        
        # all other moves illegal
        return False

    def move(self, player: Player, to_id: LocationId) -> None:
        """ Updates hallway occupancy and player position. """
        
        # save source location
        from_id = player.position

        # validate move
        if not self.is_move_legal(from_id, to_id):
            raise ValueError(f"Illegal move from {from_id} to {to_id}.")
        
        # free hallway if source location
        if from_id in self._hallway_by_id:
            source_hallway = self._hallway_by_id[from_id]
            if source_hallway.occupied_by == player.id:
                source_hallway.occupied_by = None

        # update target hallway to be occupied by player entering
        if to_id in self._hallway_by_id:
            target_hallway = self._hallway_by_id[to_id]
            
            # extra confirmation that hallway is not occupied
            if target_hallway.occupied_by is not None:
               raise ValueError(f"Hallway {to_id} is already occupied by {target_hallway.occupied_by}.")

            target_hallway.occupied_by = player.id

        # update player position
        player.position = to_id


def build_standard_board() -> Board:
    """ Builds and returns the 3x3 Clue-less board"""
    rooms: Set[Room] = {
        Room("R00", "Kitchen",        doors=("H01",),              secret_passage_to="R22"),
        Room("R01", "Ballroom",       doors=("H01", "H02", "H04")),
        Room("R02", "Conservatory",   doors=("H02",),              secret_passage_to="R20"),
        Room("R10", "Dining Room",    doors=("H03", "H06")),
        Room("R11", "Billiard Room",  doors=("H04", "H06", "H07", "H09")),
        Room("R12", "Library",        doors=("H05", "H07")),
        Room("R20", "Lounge",         doors=("H08",),              secret_passage_to="R02"),
        Room("R21", "Hall",           doors=("H08", "H09", "H10")),
        Room("R22", "Study",          doors=("H10",),              secret_passage_to="R00"),
    }

    hallways: Set[Hallway] = {
        Hallway("H01", "Between Kitchen and Ballroom",         between=("R00", "R01")),
        Hallway("H02", "Between Ballroom and Conservatory",    between=("R01", "R02")),
        Hallway("H03", "Between Kitchen and Dining Room",      between=("R00", "R10")),
        Hallway("H04", "Between Ballroom and Billiard Room",   between=("R01", "R11")),
        Hallway("H05", "Between Conservatory and Library",     between=("R02", "R12")),
        Hallway("H06", "Between Dining Room and Billiard Room",between=("R10", "R11")),
        Hallway("H07", "Between Billiard Room and Library",    between=("R11", "R12")),
        Hallway("H08", "Between Dining Room and Lounge",       between=("R10", "R20")),
        Hallway("H09", "Between Billiard Room and Hall",       between=("R11", "R21")),
        Hallway("H10", "Between Library and Study",            between=("R12", "R22")),
        Hallway("H11", "Between Lounge and Hall",              between=("R20", "R21")),
        Hallway("H12", "Between Hall and Study",               between=("R21", "R22")),
    }

    return Board(rooms=rooms, hallways=hallways)




