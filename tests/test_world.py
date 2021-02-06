import json
import os
import pytest
from textgame.world import World


BASEDIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def resources():
    resources = {}
    with open(os.path.join(BASEDIR, "resources", "rooms.json")) as f:
        resources["rooms"] = json.load(f)
    return resources


class TestWorld:

    def test_load_resources(self, resources):
        world = World()
        world.load_resources(os.path.join(BASEDIR, "resources"))
        assert world.room("field_0").description == resources["rooms"]["field_0"]["descript"]
        assert world.room("field_0").doors["south"] == world.room("field_1")

    def test_load_resources_exception(self):
        world = World()
        with pytest.raises(NotADirectoryError) as _:
            world.load_resources("doesnotexist")
        with pytest.raises(Exception) as e:
            world.load_resources(os.path.join(BASEDIR, "resources"), log_traceback=True)
        assert e.typename == "JSONDecodeError"
