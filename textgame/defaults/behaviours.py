from functools import wraps
from typing import Callable, List, Dict, Any
from ..state import State
from ..things import Creature

import logging

logger = logging.getLogger("textgame.defaults.behaviours")
logger.addHandler(logging.NullHandler())


def require_alive(func: Callable) -> Callable:
    """
    decorator for behaviour function that makes the behaviour return immediately if the creature is not alive
    """

    @wraps(func)
    def decorated(creature, state, *args, **kwargs):
        if not creature.alive:
            return
        return func(creature, state, *args, **kwargs)

    return decorated


@require_alive
def randomappearance(
    creature: Creature, state: State, probability: float, rooms: List[str]
):
    """
    spawns a creature in the same place as the player, but it vanishes after one step
    """
    logger.debug(f"calling the randomappearance of {creature.id!r}")
    # check if the creature is in a room with the player
    if creature.id in state.player_location.creatures:
        # put the creature inside the storage room
        state.get_room("storage_room").creatures.add(creature)
    elif state.random.random() < probability and any(
        r in state.player_location.id for r in rooms
    ):
        state.player_location.creatures.add(creature)


@require_alive
def randomwalk(creature: Creature, state: State, mobility: float):
    logger.debug(f"calling randomwalk behaviour of {creature.id!r}")
    # get the creature's current room
    room = state.get_location_of(creature)
    if not room:
        logging.debug(
            f"the location of the creature {creature.id!r} could not be found, skipping randomwalk"
        )
        return

    connections = list(room.get_open_connections().values())
    if state.random.random() < mobility:
        next_location = state.random.choice(connections)
        logging.debug(f"changing location of {creature.id!r} to {next_location.id!r}")
        next_location.creatures.add(creature)


@require_alive
def randomspawn_once(
    creature: Creature, state: State, probability: float, rooms: List[str]
):
    """randomly spawns in one of the rooms."""
    # only spawn creatures that are in the storage_room
    if (
        not hasattr(creature, "spawned")
        and not getattr(creature, "spawned", False)
        and state.random.random() < probability
    ):
        room = state.get_room(state.random.choice(rooms))
        logger.debug(f"spawning {creature.id!r} into {room.id!r}")
        room.creatures.add(creature)
