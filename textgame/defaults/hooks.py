from re import L
from typing import Callable, Iterable, Type, List
from ..things import Creature
from ..state import State

import logging
logger = logging.getLogger("textgame.defaults.hooks")
logger.addHandler(logging.NullHandler())


def iter_creatures(state: State, types: List[Type] = None) -> Iterable[Creature]:
    """
    helper function to iterate over all creatures that belong to any of types
    """
    types = types or []
    for room in state.rooms.values():
        for creature in list(room.creatures.values()):
            # return only creatures that have either of the specified types or all of them
            if not types or any(isinstance(creature, t) for t in types):
                yield creature


def singlebehaviourhook(behaviourname: str) -> Callable:
    def hook(state: State):
        for creature in iter_creatures(state):
            if behaviourname in creature.behaviours:
                creature.call_behaviour(behaviourname, state)

    return hook