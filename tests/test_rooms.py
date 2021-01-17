import pytest
from unittest.mock import MagicMock
from textgame.room import Room
from textgame.globals import DESCRIPTIONS, MOVING


@pytest.fixture
def roominfo_00():
    return dict(
        descript="some long description",
        sdescript="some description",
        value=3,
        dark={"now": False, "always": False},
        sound="some sound",
        hint="some hint",
        hint_value=7,
        errors={"north": "you cant go south"},
        doors={"west": Room("test_01")},
        hiddendoors={"north": Room("test_02")},
        locked={"west": {"closed": True, "key": 123}},
        dir_descriptions={"west": "you go west"},
    )

@pytest.fixture
def room_00(roominfo_00):
    room_00 = Room("room_00")
    room_00.fill_info(**roominfo_00)
    return room_00


class TestRoom:

    def test_describe(self, roominfo_00, room_00):
        assert room_00.describe() == roominfo_00["descript"]
        room_00.visit()
        assert room_00.describe() == roominfo_00["sdescript"]
        room_00.dark["now"] = True
        assert room_00.describe() == DESCRIPTIONS.DARK_L

    def test_locked(self, roominfo_00, room_00):
        assert room_00.is_locked("west")
        assert not room_00.is_locked("south")
        assert room_00.get_door_code("west") == roominfo_00["locked"]["west"]["key"]
        assert room_00.get_door_code("east") is None

    def test_describe_way(self, roominfo_00, room_00):
        assert room_00.describe_way_to("south") == ""
        assert room_00.describe_way_to("west") == roominfo_00["dir_descriptions"]["west"]

    def test_connection(self, roominfo_00, room_00):
        assert room_00.get_connection("west") == roominfo_00["doors"]["west"]
        assert room_00.get_connection("up") == None

    def test_describe_error(self, roominfo_00, room_00):
        assert room_00.describe_error("north") == roominfo_00["errors"]["north"]
        assert room_00.describe_error("down") == MOVING.FAIL_CANT_GO

    def test_restrictions(self, roominfo_00, room_00):
        player = MagicMock()
        player.look = MagicMock(return_value="great hall")
        assert room_00.check_restrictions(player) == ""
        special_func = lambda player: player.look()
        room_00.set_specials(special_func)
        assert room_00.check_restrictions(player) == "great hall"
        assert player.look.called
