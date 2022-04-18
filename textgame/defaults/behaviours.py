from dataclasses import dataclass, field
from functools import wraps
from typing import List
from ..state import State
from ..things import Creature, Behaviour
from ..messages import m

import logging

logger = logging.getLogger("textgame.defaults.behaviours")
logger.addHandler(logging.NullHandler())


@dataclass
class InRooms:
    """helper class that behaviours can inherit from that lets users define either `rooms` or `room_patterns`
    this class provides the method `get_room_ids` to compute a complete list of room ids based on rooms and room_patterns
    """

    rooms: List[str] = field(default_factory=list)
    room_patterns: List[str] = None
    _computed: bool = field(default=False, init=False, repr=False)

    def get_room_ids(self, state: State) -> List[str]:
        """find out list of rooms from rooms and room_patterns"""
        # compute only once
        if not self._computed and self.room_patterns:
            rooms_from_patterns = [
                rid
                for rid in state.rooms.keys()
                if any(p in rid for p in self.room_patterns)
            ]
            self.rooms.extend(rooms_from_patterns)
            self._computed = True
        return self.rooms


@dataclass
class RandomAppearance(InRooms, Behaviour):
    probability: float = 0

    def run(self, creature: Creature, state: State):
        """
        spawns a creature in the same place as the player, but it vanishes after one step
        """
        logger.debug(f"calling the randomappearance of {creature.id!r}")
        # check if the creature is in a room with the player
        if creature.id in state.player_location.creatures:
            # put the creature inside the storage room
            state.get_room("storage_room").creatures.add(creature)
        elif (
            state.random.random() < self.probability
            and state.player_location in self.get_room_ids(state)
        ):
            state.player_location.creatures.add(creature)


@dataclass
class RandomWalk(Behaviour):
    mobility: float

    def run(self, creature: Creature, state: State):
        logger.debug(f"calling randomwalk behaviour of {creature.id!r}")
        # get the creature's current room
        room = state.get_location_of(creature)
        if not room:
            logging.debug(
                f"the location of the creature {creature.id!r} could not be found, skipping randomwalk"
            )
            return

        connections = list(room.get_open_connections().values())
        if state.random.random() < self.mobility:
            next_location = state.random.choice(connections)
            logging.debug(
                f"changing location of {creature.id!r} to {next_location.id!r}"
            )
            next_location.creatures.add(creature)


@dataclass
class RandomSpawnOnce(InRooms, Behaviour):
    probability: float = 0

    def run(self, creature: Creature, state: State):
        """randomly spawns in one of the rooms."""
        if state.random.random() < self.probability:
            room_id = state.random.choice(self.get_room_ids(state))
            room = state.get_room(room_id)
            logger.debug(f"spawning {creature.id!r} into {room.id!r}")
            room.creatures.add(creature)
            self.switch_off()


@dataclass
class Monologue(Behaviour):
    sentences: List[str]
    index: int = 0

    def run(self, _creature, _state) -> m:
        msg = m(self.sentences[self.index])
        # get stuck at the last sentence
        self.index = min(self.index + 1, len(self.sentences) - 1)
        return msg
