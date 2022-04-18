from functools import wraps
from typing import Callable, List, Optional
from ..state import State
from ..things import Creature, Behaviour
from ..messages import m

import logging

logger = logging.getLogger("textgame.defaults.behaviours")
logger.addHandler(logging.NullHandler())


class RandomAppearance(Behaviour):
    parameters = ["probability", "rooms"]

    def run(self, creature: Creature, state: State):
        """
        spawns a creature in the same place as the player, but it vanishes after one step
        """
        logger.debug(f"calling the randomappearance of {creature.id!r}")
        # check if the creature is in a room with the player
        if creature.id in state.player_location.creatures:
            # put the creature inside the storage room
            state.get_room("storage_room").creatures.add(creature)
        elif state.random.random() < self.params["probability"] and any(
            r in state.player_location.id for r in self.params["rooms"]
        ):
            state.player_location.creatures.add(creature)


class RandomWalk(Behaviour):
    parameters = ["mobility"]

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
        if state.random.random() < self.params["mobility"]:
            next_location = state.random.choice(connections)
            logging.debug(
                f"changing location of {creature.id!r} to {next_location.id!r}"
            )
            next_location.creatures.add(creature)


class RandomSpawnOnce(Behaviour):
    parameters = ["rooms"]

    def run(self, creature: Creature, state: State):
        """randomly spawns in one of the rooms."""
        # only spawn creatures that are in the storage_room
        if (
            not hasattr(creature, "spawned")
            and not getattr(creature, "spawned", False)
            and state.random.random() < self.params["probability"]
        ):
            room = state.get_room(state.random.choice(self.params["rooms"]))
            logger.debug(f"spawning {creature.id!r} into {room.id!r}")
            room.creatures.add(creature)
