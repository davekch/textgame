import pytest
from unittest.mock import MagicMock
from textgame.player import Player, register, timeless
from textgame.parser import Parser
from textgame.world import World
from textgame.game import Game
from textgame.globals import MOVING, ACTION


@pytest.fixture
def rooms():
    return {
        "field_0": {
            # long description
            "descript": "You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest reaches to the east.",
            # short description, will be printed if the player has already been here
            "sdescript": "You are in a wide open field.",
            # how much the player's score will increase when this room is first visited
            "value": 0,
            # connections to other rooms
            "doors": {"north": "field_2", "south": "field_1"}
        },
        "field_1": {
            "descript": "You are in a wide rocky pit. An aisle leads upwards to the north.",
            "sdescript": "You're in the rocky pit.",
            # these messages will be printed if the player tries to go in the corresponding direction
            "errors": {
                "south": "The slope is too steep here.",
                "west": "The slope is too steep here.",
                "east": "The slope is too steep here."
            },
            "doors": {"north": "field_0", "up": "field_0"},
            # this will only be printed if the player leaves this room in the given direction
            "dir_descriptions": {"up": "You spread your wings and start to fly."},
            "locked": {"north":{"closed":True, "key":123}},
            "hint": "here's my special hint for you.",
            "hint_value": 7
        },
        "field_2": {
            "descript": "You are in a clear birch grove. A small stream flows by.",
            "sdescript": "You are in the birch grove.",
            # does the player need a source of light to be able to see?
            "dark": {"always": True, "now": True},
            # this will be printed if the player types "listen"
            "sound": "You hear the sound of water splashing.",
            "doors": {"south": "field_0"}
        }
    }

@pytest.fixture
def items():
    return {
        "key": {
            "description": "A key lies around.",
            "name": "key",
            "key": 123,
            "initlocation": "field_0"
        },
        "diamond": {
            "description": "A sparkling diamond lies around!",
            "name": "diamond",
            "initlocation": "field_1"
        }
    }


@pytest.fixture
def game(rooms, items):
    world = World(rooms=rooms, items=items)
    player = Player(world, world.room("field_0"))
    parser = Parser()
    parser.set_actionmap(player.get_registered_methods())
    parser.check_synonyms()
    return Game(player, parser)


class TestGameplay:

    def test_go(self, game, rooms, items):
        expected = rooms["field_1"]["descript"] + "\n" + items["diamond"]["description"] + "\n"
        assert game.play("go south") == expected
        assert game.play("w") == rooms["field_1"]["errors"]["west"] + "\n"
        assert game.play("north") == MOVING.FAIL_DOOR_LOCKED + "\n"

    def test_keys(self, game, items):
        for c in ["take key", "s", "open north"]:
            response = game.play(c)
        assert response.strip() == ACTION.NOW_OPEN.format("open")
        game.play("n")  # can now walk back
        assert game.player.location.id == "field_0"
        game.play("s")
        assert game.play("open north").strip() == ACTION.ALREADY_OPEN
        assert game.play("close north").strip() == ACTION.NOW_OPEN.format("lock")
        game.play("drop key")
        assert game.play("open north").strip() == ACTION.FAIL_NO_KEY

    def test_walkthrough(self, game):
        walkthrough = [('look', 'You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest reaches to the east.\nA key lies around.\n'), ('take keys', 'I see no keys here.\n'), ('take key', 'You carry now a key.\n'), ('n', "It's pitch dark here. You can't see anything. Anytime soon, you'll probably get attacked by some night creature.\n"), ('go back', 'You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest reaches to the east.\n'), ('s', 'You are in a wide rocky pit. An aisle leads upwards to the north.\nA sparkling diamond lies around!\n'), ('w', 'The slope is too steep here.\n'), ('take diamond', 'You carry now a diamond.\n'), ('inventory', 'You are now carrying:\n A key\n A diamond\n'), ('drop ', 'Please specify an item you want to drop.\n'), ('drop key', 'Dropped.\n'), ('take all', 'You carry now a key.\n'), ('n', 'The door is locked.\n'), ('up', 'You spread your wings and start to fly.\nYou are in a wide open field.\n'), ('back', "I don't understand that.\n"), ('go back', "You're in the rocky pit.\n"), ('open door', "I can only open doors if you tell me the direction. Eg. 'open west'.\n"), ('open west', 'There is no door in this direction.\n'), ('open north', 'You take the key and open the door.\n'), ('n', 'You are in a wide open field.\n'), ('s', "You're in the rocky pit.\n"), ('close north', 'You take the key and lock the door.\n'), ('drop key', 'Dropped.\n'), ('go north', 'The door is locked.\n'), ('score', 'Your score is 5.\n')]
        for command, reply in walkthrough:
            assert game.play(command) == reply


class TestWorldtime:

    def test_time(self):
        world = World()
        player = Player(world, MagicMock())
        parser = Parser()
        parser.set_actionmap(player.get_registered_methods())
        game = Game(player, parser)
        assert game.world.time == 0
        game.play("look")
        assert game.world.time == 1

    def test_timeless(self):
        class MyPlayer(Player):
            @timeless
            @register("fart")
            def fart(self):
                return "prrrfft"

        world = World()
        player = MyPlayer(world, MagicMock())
        parser = Parser()
        parser.set_actionmap(player.get_registered_methods())
        game = Game(player, parser)
        assert game.world.time == 0
        game.play("fart")
        assert game.world.time == 0
