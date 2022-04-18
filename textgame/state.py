from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional
from .room import Room
from .things import Item


class PlayerStatus(Enum):
    NORMAL = auto()
    TRAPPED = auto()
    FIGHTING = auto()
    DEAD = auto()


@dataclass
class State:
    rooms: Dict[str, Room]
    player_location: Room
    player_location_old: Room = None
    inventory: Dict[str, Item] = field(default_factory=dict)
    player_status: PlayerStatus = PlayerStatus.NORMAL
    misc: Dict[str, Any] = field(default_factory=dict)
    score: int = 0
    time: int = 0

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)
