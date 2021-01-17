from unittest.mock import MagicMock
from textgame.player import Player, register
from textgame.globals import MOVING


class TestPlayer:

    def test_register(self):
        class MyPlayer(Player):
            @register("lol")
            def laugh(self):
                return 1234

        myplayer = MyPlayer(MagicMock(), MagicMock())
        methodmap = myplayer.get_registered_methods()
        assert "lol" in methodmap
        assert methodmap["lol"]() == 1234
        assert "go" in methodmap  # check inheritance

    def test_go(self):
        location = MagicMock()
        location.is_locked = MagicMock(return_value=False)
        location.describe_way_to = MagicMock(return_value="dir description")
        destination = MagicMock()
        destination.check_restrictions = MagicMock(return_value="restriction")
        destination.is_dark = MagicMock(return_value=False)
        destination.describe = MagicMock(return_value="description")
        location.get_connection = MagicMock(return_value=destination)
        player = Player(MagicMock(), location)
        assert player.go("wurst") == MOVING.FAIL_NOT_DIRECTION
        assert player.go("") == MOVING.FAIL_WHERE
        assert player.go("north") == "dir description\nrestrictiondescription"
