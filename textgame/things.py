from dataclasses import dataclass, field
from typing import Type, TypeVar, Dict, Any
from .messages import m
from .registry import behavior_registry
from .exceptions import ConfigurationError


@dataclass
class Thing:
    id: str
    name: str
    description: str
    initlocation: str

    def describe(self) -> m:
        return m(self.description)


@dataclass
class Item(Thing):
    value: int = 0
    takable: bool = True


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class Weapon(Item):
    strength: int = 0


@dataclass
class Creature(Thing):
    dead_description: str = None
    alive: bool = True
    # behaviours could look like this: {"spawn": {"probability": 0.2, "rooms": ["field_0", "field_1"]}}
    behaviours: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def call_behaviour(self, behaviourname: str, state):
        if behaviourname not in self.behaviours:
            raise ConfigurationError(f"the behaviour {behaviourname!r} is not defined for the Creature {self!r}")
        params = self.behaviours[behaviourname]
        if behaviourname not in behavior_registry:
            raise ConfigurationError(f"no behaviour {behaviourname!r} is registered")
        behaviour = behavior_registry[behaviourname]
        return behaviour(self, state, **params)

    def behave(self, state):
        """
        call all functions specified in behaviours with the given parameters
        """
        for name in self.behaviours:
            self.call_behaviour(name, state)

    def die(self):
        self.alive = False
        self.description = self.dead_description or self.description

    
@dataclass
class Monster(Creature):
    strength: int = 0

