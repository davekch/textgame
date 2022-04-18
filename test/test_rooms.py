import pytest
from textgame.room import Room
from textgame.messages import DESCRIPTIONS, MOVING


@pytest.fixture
def roominfo_00():
    return dict(
        ID="room_00",
        description="some long description",
        shortdescription="some description",
        value=3,
        dark={"now": False, "always": False},
        sound="some sound",
        hint="some hint",
        hint_value=7,
        errors={"north": "you cant go south"},
        doors={"west": "test_01"},
        hiddendoors={"north": "test_02"},
        locked={"west": {"locked": True, "key": 123}},
        dir_descriptions={"west": "you go west"},
    )


@pytest.fixture
def room_00(roominfo_00):
    return Room(**roominfo_00)


class TestRoom:
    def test_locked(self, roominfo_00, room_00):
        assert room_00.is_locked("west")
        assert not room_00.is_locked("south")
        assert room_00.get_door_code("west") == roominfo_00["locked"]["west"]["key"]
        assert room_00.get_door_code("east") is None

    def test_describe_way(self, roominfo_00, room_00):
        assert room_00.describe_way_to("south") == ""
        assert (
            room_00.describe_way_to("west") == roominfo_00["dir_descriptions"]["west"]
        )

    def test_connection(self, roominfo_00, room_00):
        assert room_00.get_connection("west") == roominfo_00["doors"]["west"]
        assert room_00.get_connection("up") == None

    def test_describe_error(self, roominfo_00, room_00):
        assert room_00.describe_error("north") == roominfo_00["errors"]["north"]
        assert room_00.describe_error("down") == MOVING.FAIL_CANT_GO
