import pytest
import json
import os
from typing import List, Dict
from textgame.loader import ItemLoader, RoomLoader, Factory
from textgame.room import Room
from textgame.items import Item, Key


BASEDIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def rooms():
    with open(os.path.join(BASEDIR, "resources", "rooms.json")) as f:
        rooms = json.load(f)
    return rooms


@pytest.fixture
def items():
    with open(os.path.join(BASEDIR, "resources", "items.json")) as f:
        items = json.load(f)
    return items


class TestLoader:

    def test_load_rooms(self, rooms: List[Dict]):
        room_objs = RoomLoader.load(rooms)
        assert isinstance(room_objs[0], Room)
    
    def test_custom_room(self, rooms: List[Dict]):

        class MyRoom(Room):
            pass
    
        Factory.register("room", MyRoom)
        room_objs = RoomLoader.load(rooms)
        assert isinstance(room_objs[0], MyRoom)

    def test_load_items(self, items: List[Dict]):
        item_objs = ItemLoader.load(items)
        assert isinstance(item_objs[0], Item)
        assert isinstance(item_objs[-1], Key)
        assert item_objs[-1].key_id == items[-1]["key_id"]
        assert len([i for i in item_objs if isinstance(i, Key)]) == 1
