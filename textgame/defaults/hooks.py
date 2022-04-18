from typing import Callable, Iterable, Type, List
from ..things import Creature
from ..state import State
from ..messages import m

import logging
logger = logging.getLogger("textgame.defaults.hooks")
logger.addHandler(logging.NullHandler())


def singlebehaviourhook(behaviourname: str) -> Callable[[State], m]:
    """
    creates a hook that calls the behaviour `behaviourname` for every creature
    """
    def hook(state: State) -> m:
        logger.debug(f"calling hook for behaviour {behaviourname!r}")
        msg = m()
        for creature in state.creatures.storage.values():
            if behaviourname in creature.behaviours:
                msg += creature.call_behaviour(behaviourname, state)
        return msg

    return hook


def time(state: State):
    state.time += 1