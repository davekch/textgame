from typing import List
from ..state import State
from ..things import Creature

import logging
logger = logging.getLogger("textgame.defaults.behaviours")
logger.addHandler(logging.NullHandler())


def randomappearance(creature: Creature, state: State, probability: float, rooms: List[str]):
    """
    spawns a creature in the same place as the player, but it vanishes after one step
    """
    logger.debug(f"calling the randomappearance of {creature.id!r}")
    # check if the creature is in a room with the player
    if creature.id in state.player_location.creatures:
        # put the creature inside the storage room
        state.get_room("storage_room").creatures.add(creature)
    elif (
        creature.alive
        and state.random.random() < probability
        and any(r in state.player_location.id for r in rooms)
    ):
        state.player_location.creatures.add(creature)


def randomwalk(creature: Creature, state: State, mobility: float):
    logger.debug(f"calling randomwalk behaviour of {creature.id!r}")
    # get the creature's current room
    room = state.get_location_of(creature)
    if not room:
        logging.debug(f"the location of the creature {creature.id!r} could not be found, skipping randomwalk")
        return
    
    connections = room.get_open_connections().values()
    if state.random.random() < mobility:
        next_location = state.random.choice(connections)
        logging.debug(f"changing location of {creature.id!r} to {next_location.id!r}")
        next_location.creatures.add(creature)