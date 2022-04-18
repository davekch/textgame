from typing import Callable, Iterable, Type, List
from ..things import Creature
from ..state import State

import logging
logger = logging.getLogger("textgame.defaults.hooks")
logger.addHandler(logging.NullHandler())


def singlebehaviourhook(behaviourname: str) -> Callable:
    def hook(state: State):
        for creature in state.creatures.storage:
            if behaviourname in creature.behaviours:
                creature.call_behaviour(behaviourname, state)

    return hook