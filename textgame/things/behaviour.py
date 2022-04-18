from __future__ import annotations
from dataclasses import dataclass, fields, field
from abc import ABC, abstractmethod
from typing import Optional, List, Type, Dict, Any
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
class Behaviour(ABC):
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
    def run(self, creature: _Behaves, state: State) -> Optional[m]:
        pass


def behavioursequence(behaviours: List[Type[Behaviour]]) -> Type[Behaviour]:
    """create a behaviour that runs each of the behaviours one after another"""

    @dataclass
    class CombinedBehaviour(*behaviours, Behaviour):
        def __post_init__(self):
            # this must be a post-init because we must not overwrite the init by the behaviours
            # initialize each behaviour
            self.behaviours: List[Behaviour] = []
            for behaviour in behaviours:
                # collect the parameters that are meant for this behaviour
                parameters = {
                    field.name: getattr(self, field.name)
                    for field in fields(behaviour)
                    if field.init
                }
                self.behaviours.append(behaviour(**parameters))

        def run(self, creature: _Behaves, state: State) -> m:
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

    return CombinedBehaviour


def behaviour_factory(behaviourname: str, params: Dict[str, Any]) -> Behaviour:
    if behaviourname not in behaviour_registry:
        raise ConfigurationError(f"behaviour {behaviourname!r} is not registered")
    behaviour_class = behaviour_registry[behaviourname]
    params_copy = params.copy()
    if "switch" not in params_copy:
        params_copy["switch"] = True
    return behaviour_class(**params_copy)


@dataclass
class _Behaves:
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
                f"the behaviour {behaviourname!r} is not defined for the Creature {self!r}"
            )
        if self.behaviours[behaviourname].is_switched_on():
            logger.debug(f"call behaviour {behaviourname!r} for creature {self.id!r}")
            return self.behaviours[behaviourname].run(self, state)

    def behave(self, state: State) -> Optional[m]:
        """
        call all functions specified in behaviours with the given parameters
        """
        msg = m()
        for name in self.behaviours:
            msg += self.call_behaviour(name, state)
        return msg
