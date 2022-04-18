from typing import Callable, List
from ..state import Daytime, PlayerStatus, State
from ..messages import INFO, m

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


def daylight(
    duration_day: int,
    duration_night: int,
    on_sunset: Callable[[State], m] = None,
    on_sunrise: Callable[[State], m] = None,
) -> m:
    """
    creates a hook that lets the sun rise and fall. only makes sense together with hooks.time
    """

    def daytimehook(state: State) -> m:
        logger.debug("handling daytime")
        msg = m()
        time = state.time % (duration_day + duration_night)
        if state.daytime == Daytime.DAY and time >= duration_day:
            logger.debug(
                f"current time is {time!r} (absolute: {state.time!r}), it's sunset"
            )
            state.daytime = Daytime.NIGHT
            msg += INFO.SUNSET
            if callable(on_sunset):
                msg += on_sunset(state)
            # turn all lights down
            for room in state.rooms.values():
                room.dark["now"] = True
        elif state.daytime == Daytime.NIGHT and time <= duration_day:
            logger.debug(
                f"current time is {time!r} (absolute: {state.time!r}), it's sunrise"
            )
            state.daytime = Daytime.DAY
            msg += INFO.SUNRISE
            if callable(on_sunrise):
                msg += on_sunrise()
            # turn all lights on
            for room in state.rooms.values():
                room.dark["now"] = room.dark["always"]
        return msg

    return daytimehook
