import pytest
import json
import os
from typing import List, Dict
from textgame.loader import CreatureLoader, ItemLoader, RoomLoader, Factory
from textgame.registry import register_behaviour
from textgame.room import Room
from textgame.things import Creature, Item, Key
from textgame.defaults import behaviours


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


@pytest.fixture
def creatures():
    with open(os.path.join(BASEDIR, "resources", "creatures.json")) as f:
        creatures = json.load(f)
    return creatures


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

    def test_load_creatures(self, creatures: List[Dict]):
        # works only if the behaviours that the creatures have are registered
        register_behaviour("randomappearance", behaviours.RandomAppearance)
        register_behaviour("randomwalk", behaviours.RandomWalk)
        register_behaviour("random_spawn_once", behaviours.RandomSpawnOnce)
        creature_objs = CreatureLoader.load(creatures)
        assert isinstance(creature_objs[0], Creature)
