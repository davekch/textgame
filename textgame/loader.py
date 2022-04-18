from json import load
from typing import List, Dict, Any, Callable
from .room import Room
from .items import Item, Key


class Factory:

    creation_funcs = {
        "room": Room,
        "item": Item,
        "key": Key,
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


class ConfigurationError(Exception):
    pass


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


class WorldBuilder:
    """class to put everything together"""

    def __init__(self, itemloader: Loader = ItemLoader, roomloader: Loader = RoomLoader):
        self.itemloader = itemloader
        self.roomloader = roomloader
    
    @staticmethod
    def build_graph(rooms: List[Room]) -> Dict[str, Room]:
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
    
    def build(self, rooms: List[Dict], items: List[Dict]) -> Dict[str, Room]:
        """load rooms and items and place the items inside the rooms. return a graph of rooms"""
        rooms = self.build_graph(self.roomloader.load(rooms))
        items = self.itemloader.load(items)
        for item in items:
            initlocation = rooms.get(item.initlocation)
            if not initlocation:
                raise ConfigurationError(
                    f"the initial location '{item.initlocation} of item '{item.name}' does not exist"
                )
            initlocation.add_item(item)
        return rooms