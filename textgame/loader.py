from dataclasses import dataclass
from itertools import chain
from json import load
from typing import List, Dict, Any, Callable, Type
from pathlib import Path
import json
import os
from .room import Room
from .things import (
    Behaviour,
    Container,
    Item,
    Key,
    Creature,
    Lightsource,
    Monster,
    Weapon,
)
from .caller import Caller, SimpleCaller
from .state import State
from .exceptions import ConfigurationError, FactoryNotFoundError
from .game import Game
from .registry import behaviour_registry

import logging

logger = logging.getLogger("textgame.loader")
logger.addHandler(logging.NullHandler())


class Factory:

    creation_funcs = {
        "room": Room,
        "item": Item,
        "key": Key,
        "weapon": Weapon,
        "lightsource": Lightsource,
        "container": Container,
        "creature": Creature,
        "monster": Monster,
    }

    @classmethod
    def register(cls, obj_type: str, creation_func: Callable[..., Any]):
        cls.creation_funcs[obj_type] = creation_func

    @classmethod
    def unregister(cls, obj_type: str):
        cls.creation_funcs.pop(obj_type, None)

    @classmethod
    def create(cls, args: Dict[str, Any], obj_type: str = None) -> Any:
        args_copy = args.copy()
        if not obj_type:
            obj_type = args_copy.pop("type")
        try:
            return cls.creation_funcs[obj_type](**args_copy)
        except KeyError:
            raise FactoryNotFoundError(f"{obj_type!r} is not a registered type")


def behaviour_factory(behaviourname: str, params: Dict[str, Any]) -> Behaviour:
    if behaviourname not in behaviour_registry:
        raise ConfigurationError(f"behaviour {behaviourname!r} is not registered")
    behaviour_class = behaviour_registry[behaviourname]
    switch = params.pop("switch", None)
    if switch is None:
        return behaviour_class(params=params)
    return behaviour_class(switch=switch, params=params)


def load_resources(path: Path, format: str = "json") -> Dict[str, List[Dict]]:
    files = [f for f in os.listdir(path) if f.endswith(format)]
    resources = {}
    for file in files:
        logger.debug(f"load resource {Path(path) / file}")
        with open(Path(path) / file) as f:
            if format == "json":
                resource = json.load(f)
            elif format == "yaml":
                import yaml

                resource = yaml.safe_load(f)
            else:
                raise NotImplementedError("can only load json or yaml")
        resources[Path(file).stem] = resource
    return resources


class Loader:

    defaultclass: str = None
    factory: Factory = Factory

    @classmethod
    def load_objs(cls, dicts: List[Dict[str, Any]], obj_type=None) -> List[Any]:
        objs = []
        for args in dicts:
            if "type" not in args and not obj_type:
                raise ConfigurationError("type is missing from object description")
            elif "type" not in args:
                objs.append(cls.factory.create(args, obj_type=obj_type))
            else:
                objs.append(cls.factory.create(args))
        return objs

    @classmethod
    def load(cls, dicts: List[Dict[str, Any]]) -> List[Any]:
        return cls.load_objs(dicts, obj_type=cls.defaultclass)


class RoomLoader(Loader):
    defaultclass = "room"


class ItemLoader(Loader):
    defaultclass = "item"


class CreatureLoader(Loader):
    defaultclass = "creature"

    @classmethod
    def load_objs(cls, dicts: List[Dict[str, Any]], obj_type=None) -> List[Creature]:
        objs = super().load_objs(dicts, obj_type)
        # build behaviour objects for the creatures
        for creature in objs:
            for behaviourname, params in list(creature.behaviours.items()):
                try:
                    behaviour = behaviour_factory(behaviourname, params)
                except ConfigurationError as error:
                    raise ConfigurationError(
                        f"an error occured while creating the creature {creature.id!r}"
                    ) from error
                # overwrite the creature's behaviour
                logger.debug(
                    f"add behaviour of type {type(behaviour)} to creature {creature.id!r}. "
                    f"behaviour is switched {'on' if behaviour.switch else 'off'}"
                )
                creature.behaviours[behaviourname] = behaviour
        return objs


class StateBuilder:
    """class to put everything together"""

    def __init__(
        self,
        state_class=State,
        itemloader: Type[Loader] = ItemLoader,
        roomloader: Type[Loader] = RoomLoader,
        creatureloader: Type[Loader] = CreatureLoader,
    ):
        self.state_class = state_class
        self.itemloader = itemloader
        self.roomloader = roomloader
        self.creatureloader = creatureloader

    @staticmethod
    def build_room_graph(rooms: List[Room]) -> Dict[str, Room]:
        """
        convert a list of rooms to a dictionary of room-ids mapping to
        room objects and also convert every room.door dict from Dict[str, str]
        to Dict[str, Room]
        """
        graph = {room.id: room for room in rooms}
        logger.debug("connect rooms")
        for room in graph.values():
            for direction in room.doors:
                if room.has_connection_in(direction):
                    room.doors[direction] = graph[room.doors[direction]]
            for direction in room.hiddendoors:
                if room.has_connection_in(direction, include_hidden=True):
                    room.hiddendoors[direction] = graph[room.hiddendoors[direction]]
        return graph

    def build(
        self,
        initial_location: str,
        rooms: List[Dict],
        items: List[Dict] = None,
        creatures: List[Dict] = None,
    ) -> State:
        """load rooms, items and creatures and place them inside the rooms. return state object"""
        # load everything
        logger.debug("create rooms")
        rooms = self.build_room_graph(self.roomloader.load(rooms))
        logger.debug("create items")
        items = self.itemloader.load(items or [])
        logger.debug("create creatures")
        creatures = self.creatureloader.load(creatures or [])
        state = self.state_class(
            rooms=rooms,
            player_location=rooms[initial_location],
            items={i.id: i for i in items},
            creatures={c.id: c for c in creatures},
        )

        # connect the room's stores to the state's storemanagers
        for room in rooms.values():
            state.items.add_store(room.items)
            state.creatures.add_store(room.creatures)
        # connect all container's stores to the state's storemanager
        for item in items:
            if isinstance(item, Container):
                state.items.add_store(item._contains)

        logger.debug("put items and creatures in their locations")
        for thing in chain(items, creatures):
            if thing.initlocation not in rooms:
                raise ConfigurationError(
                    f"the initial location {thing.initlocation!r} of thing {thing.name!r} does not exist"
                )
            if isinstance(thing, Item):
                rooms[thing.initlocation].items.add(thing)
            elif isinstance(thing, Creature):
                rooms[thing.initlocation].creatures.add(thing)

        return state


@dataclass
class GameBuilder:
    game_class: Type[Game] = Game
    caller_class: Type[Caller] = SimpleCaller

    def build(self, state: State, **kwargs) -> Game:
        return self.game_class(
            initial_state=state, caller=self.caller_class(), **kwargs
        )
