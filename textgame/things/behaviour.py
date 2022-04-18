from __future__ import annotations
from dataclasses import dataclass, fields, field
from abc import ABC, abstractmethod
from typing import Generic, Optional, List, Type, Dict, Any, TypeVar
from .base import Thing
from ..messages import m
from ..registry import behaviour_registry
from ..exceptions import ConfigurationError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # State is only used as a type-hint in this file
    from ..state import State

import logging

logger = logging.getLogger("textgame.things")
logger.addHandler(logging.NullHandler())


@dataclass
class _Behaves(Thing):
    # behaviours could look like this: {"spawn": {"probability": 0.2, "rooms": ["field_0", "field_1"]}}
    behaviours: Dict[str, Behaviour] = field(default_factory=dict)

    def __post_init__(self):
        # turn the behaviours into actual behaviour objects
        for behaviourname, params in list(self.behaviours.items()):
            try:
                behaviour = behaviour_factory(behaviourname, params)
            except ConfigurationError as error:
                raise ConfigurationError(
                    f"an error occured while creating the creature {self.id!r}"
                ) from error
            # overwrite the creature's behaviour
            logger.debug(
                f"add behaviour of type {type(behaviour)} to creature {self.id!r}. "
                f"behaviour is switched {'on' if behaviour.switch else 'off'}"
            )
            self.behaviours[behaviourname] = behaviour

    def call_behaviour(self, behaviourname: str, state: State) -> Optional[m]:
        if behaviourname not in self.behaviours:
            raise ConfigurationError(
                f"the behaviour {behaviourname!r} is not defined for the Creature {self.id!r}"
            )
        if self.behaviours[behaviourname].is_switched_on():
            logger.debug(f"call behaviour {behaviourname!r} for creature {self.id!r}")
            return self.behaviours[behaviourname].run(self, state)
        return None

    def behave(self, state: State) -> Optional[m]:
        """
        call all functions specified in behaviours with the given parameters
        """
        msg = m()
        for name in self.behaviours:
            msg += self.call_behaviour(name, state)
        return msg


CanBehave = TypeVar("CanBehave", bound=_Behaves)

# this is a bug in mypy, so ignore it for now
# https://github.com/python/mypy/issues/5374
@dataclass  # type: ignore
class Behaviour(ABC, Generic[CanBehave]):
    switch: bool
    # note: switch gets a default of True by loader.behaviour_factory if nothing
    # else is set. this is ugly but necessary because default-values in dataclass
    # base classes mess up inheritance. when updating to python3.10, use
    # @dataclass(kw_only=True) instead

    def switch_on(self):
        self.switch = True

    def switch_off(self):
        self.switch = False

    def toggle(self):
        if self.is_switched_on():
            self.switch_off()
        else:
            self.switch_on()

    def is_switched_on(self) -> bool:
        return self.switch

    @abstractmethod
    def run(self, creature: CanBehave, state: State) -> Optional[m]:
        pass


# todo: maybe this should go in textgame.defaults.behaviours?
@dataclass
class BehaviourSequence(Behaviour):
    sequence: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.behaviours: List[Behaviour] = []
        for behaviourdata in self.sequence:
            [(behaviourname, parameters)] = behaviourdata.items()
            behaviour = behaviour_factory(behaviourname, parameters)
            self.behaviours.append(behaviour)

    def run(self, creature: CanBehave, state: State) -> Optional[m]:
        for behaviour in self.behaviours:
            if behaviour.is_switched_on():
                msg = behaviour.run(creature, state)
                break
        else:
            # no break, this means all behaviours are switched off
            self.switch_off()
            msg = m()
        return msg

    def switch_on(self):
        super().switch_on()
        for behaviour in self.behaviours:
            behaviour.switch_on()

    def switch_off(self):
        super().switch_off()
        for behaviour in self.behaviours:
            behaviour.switch_off()


def behaviour_factory(behaviourname: str, params: Dict[str, Any]) -> Behaviour:
    if behaviourname not in behaviour_registry:
        raise ConfigurationError(f"behaviour {behaviourname!r} is not registered")
    behaviour_class = behaviour_registry[behaviourname]
    params_copy = params.copy()
    if "switch" not in params_copy:
        params_copy["switch"] = True
    return behaviour_class(**params_copy)
