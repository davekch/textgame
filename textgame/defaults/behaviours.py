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
    logger.debug(f"calling the singleencounterbehaviour of {creature.id!r}")
    # check if the creature is in a room with the player
    if creature.id in state.player_location.creatures:
        state.player_location.pop_creature(creature.id)
        state.get_room("storage_room").add_creature(creature)
    elif (
        creature.alive
        and state.random.random() < probability
        and any(r in state.player_location.id for r in rooms)
    ):
        state.get_room("storage_room").pop_creature(creature.id)
        state.player_location.add_creature(creature)