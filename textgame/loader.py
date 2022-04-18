from dataclasses import dataclass
from itertools import chain
from json import load
from typing import List, Dict, Any, Callable, Type
from pathlib import Path
import json
from copy import deepcopy
import os
from .room import Room
from .things import (
    Container,
    _Contains,
    Item,
    Key,
    Creature,
    Lightsource,
    Monster,
    Thing,
    Weapon,
)
from .caller import Caller, SimpleCaller
from .state import State
from .exceptions import ConfigurationError, FactoryNotFoundError
from .game import Game
from .registry import behaviour_registry, Registry

import logging

logger = logging.getLogger("textgame.loader")
logger.addHandler(logging.NullHandler())


class Factory:

    creation_funcs = Registry(
        {
            "room": Room,
            "item": Item,
            "key": Key,
            "weapon": Weapon,
            "lightsource": Lightsource,
            "container": Container,
            "creature": Creature,
            "monster": Monster,
        }
    )

    @classmethod
    def register(cls, obj_type: str, creation_func: Callable[..., Any] = None):
        return cls.creation_funcs.register(obj_type, creation_func)

    @classmethod
    def unregister(cls, obj_type: str):
        cls.creation_funcs.unregister(obj_type)

    @classmethod
    def create(cls, args: Dict[str, Any], obj_type: str = None) -> Any:
        args_copy = args.copy()
        if not obj_type:
            obj_type = args_copy.pop("type")
        try:
            return cls.creation_funcs[obj_type](**args_copy)
        except KeyError:
            raise FactoryNotFoundError(f"{obj_type!r} is not a registered type")


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
    def load_objs(cls, dicts: List[Dict[str, Any]], obj_type=None) -> List[Thing]:
        # make sure to not accidentally mutate the original list
        dicts = deepcopy(dicts)
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
    def load(cls, dicts: List[Dict[str, Any]]) -> List[Thing]:
        return cls.load_objs(dicts, obj_type=cls.defaultclass)


class RoomLoader(Loader):
    defaultclass = "room"


class ItemLoader(Loader):
    defaultclass = "item"


class CreatureLoader(Loader):
    defaultclass = "creature"


@dataclass
class StateBuilder:
    """class to put everything together"""

    state_class: Type = State
    itemloader: Type[Loader] = ItemLoader
    roomloader: Type[Loader] = RoomLoader
    creatureloader: Type[Loader] = CreatureLoader

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

        # connect all stores to the state's storemanagers
        # iterate also over items and creatures, as they might be containers too
        for container in chain(rooms.values(), items, creatures):
            if isinstance(container, _Contains):
                state.things_manager.add_store(container.things)

        logger.debug("put items and creatures in their locations")
        for thing in chain(items, creatures):
            if thing.initlocation not in rooms:
                raise ConfigurationError(
                    f"the initial location {thing.initlocation!r} of thing {thing.name!r} does not exist"
                )
            rooms[thing.initlocation].things.add(thing)

        return state


@dataclass
class GameBuilder:
    game_class: Type[Game] = Game
    caller_class: Type[Caller] = SimpleCaller

    def build(self, state: State, **kwargs) -> Game:
        return self.game_class(
            initial_state=state, caller=self.caller_class(), **kwargs
        )
