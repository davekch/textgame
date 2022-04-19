from typing import Callable, List
from ..state import Daytime, PlayerStatus, State
from ..things import Monster, _Behaves
from ..messages import m
from ..defaults.words import INFO

import logging

logger = logging.getLogger("textgame.defaults.hooks")
logger.addHandler(logging.NullHandler())


def singlebehaviourhook(behaviourname: str) -> Callable[[State], m]:
    """
    creates a hook that calls the behaviour `behaviourname` for every thing that can behave
    """

    def hook(state: State) -> m:
        logger.debug(f"calling hook for behaviour {behaviourname!r}")
        msg = m()
        for behaves in state.things_manager.storage.values():
            # iterate over all things and select the ones which can behave
            if not isinstance(behaves, _Behaves):
                continue
            if behaviourname in behaves.behaviours:
                msg += behaves.call_behaviour(behaviourname, state)
        return msg

    return hook


def time(state: State):
    state.time += 1


def events(state: State) -> m:
    """call the events that were set by state.set_event and that are ready"""
    msg = m()
    for event in state.pop_ready_events():
        logger.debug(f"calling event {event}")
        msg += event.call(state)
    return msg


def daylight(
    duration_day: int,
    duration_night: int,
    on_sunset: Callable[[State], m] = None,
    on_sunrise: Callable[[State], m] = None,
) -> Callable[[State], m]:
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
                msg += on_sunrise(state)
            # turn all lights on
            for room in state.rooms.values():
                room.dark["now"] = room.dark["always"]
        return msg

    return daytimehook


def manage_fights(state: State) -> m:
    logger.debug("manage ongoing fights")
    msg = m()
    for monster in state.player_location.things.values(filter=[Monster]):
        if not monster.alive:
            continue

        logger.debug(f"calculate fight outcome with monster {monster.id!r}")
        if monster.health <= 0:
            monster.die()
            msg += m(monster.win_message)
        else:
            damage = monster.calculate_damage(state.random)
            logger.debug(f"monster has damage of {damage!r}")
            state.health -= damage
            if state.health <= 0:
                state.player_status = PlayerStatus.DEAD
                msg += m(monster.loose_message)
                break
            else:
                msg += m(monster.fight_message)

    return msg
