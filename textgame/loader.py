from itertools import chain
from json import load
from typing import List, Dict, Any, Callable
from .room import Room
from .things import Item, Key, Creature
from .state import State
from .exceptions import ConfigurationError


class Factory:

    creation_funcs = {
        "room": Room,
        "item": Item,
        "key": Key,
        "creature": Creature,
    }

    @classmethod
    def register(cls, obj_type: str, creation_func: Callable[..., Any]):
        cls.creation_funcs[obj_type] = creation_func

    @classmethod
    def unregister(cls, obj_type: str):
        cls.creation_funcs.pop(obj_type, None)

    @classmethod
    def create(cls, args: Dict[str, Any], obj_type: str=None) -> Any:
        args_copy = args.copy()
        if not obj_type:
            obj_type = args_copy.pop("type")
        return cls.creation_funcs[obj_type](**args_copy)


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


class StateBuilder:
    """class to put everything together"""

    def __init__(
        self,
        state_class = State,
        itemloader: Loader = ItemLoader,
        roomloader: Loader = RoomLoader,
        creatureloader: Loader = CreatureLoader
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
        creatures: List[Dict] = None
    ) -> State:
        """load rooms and items and place the items inside the rooms. return a graph of rooms"""
        # load everything
        rooms = self.build_room_graph(self.roomloader.load(rooms))
        items = self.itemloader.load(items or [])
        creatures = self.creatureloader.load(creatures or [])
        state = self.state_class(
            rooms=rooms,
            player_location=rooms[initial_location],
            items={i.id: i for i in items},
            creatures={c.id: c for c in creatures}
        )
        # connect the room's stores to the state's storemanagers
        for room in rooms.values():
            state.items.add_store(room.items)
            state.creatures.add_store(room.creatures)

        # put items and creatures in their locations
        for thing in chain(items, creatures):
            if thing.initlocation not in rooms:
                raise ConfigurationError(
                    f"the initial location '{thing.initlocation} of thing '{thing.name}' does not exist"
                )
            if isinstance(thing, Item):
                rooms[thing.initlocation].items.add(thing)
            elif isinstance(thing, Creature):
                rooms[thing.initlocation].creatures.add(thing)

        return state