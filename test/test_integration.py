from textgame.game import Game
from textgame.parser import SimpleParser
from textgame.loader import StateBuilder
from textgame.state import State
from textgame.messages import ACTION, MOVING, EnterYesNoLoop, m, INFO
from textgame.room import Room
from textgame.state import State
from textgame.registry import (
    register_command,
    register_precommandhook,
    register_postcommandhook,
    precommandhook_registry,
    postcommandhook_registry,
    unregister_postcommandhook,
    unregister_precommandhook,
)
from textgame.defaults import commands
from typing import Dict
import json
import pytest
import os


BASEDIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def resources() -> Dict:
    with open(os.path.join(BASEDIR, "resources", "rooms.json")) as f:
        room_dicts = json.load(f)
    with open(os.path.join(BASEDIR, "resources", "items.json")) as f:
        item_dicts = json.load(f)
    return {
        "rooms": room_dicts,
        "items": item_dicts,
    }


@pytest.fixture
def game(resources) -> Game:
    state = StateBuilder().build(initial_location="field_0", **resources)
    parser = SimpleParser()
    return Game(initial_state=state, parser=parser)


class TestGamePlay:

    def test_look(self, game: Game):
        expected = (
            str(game.state.rooms["field_0"].description) + "\n"
            + str(game.state.rooms["field_0"].items.get("diamond").description)
        )
        assert game.play("look") == expected
    
    def test_custom_command(self, game: Game):
        @register_command("scream")
        def scream(noun: str, state: State) -> m:
            return m(f"{noun.upper()}!!!")
        
        assert game.play("scream hello") == "HELLO!!!"
    
    def test_yesno(self, game: Game):
        @register_command("jump")
        def jump(_noun: str, state: State) -> EnterYesNoLoop:
            return EnterYesNoLoop(
                question=m("Really?"),
                yes=m("You said yes."),
                no=m("You said no.")
            )
        
        assert game.play("jump") == "Really?"
        assert game.play("go west") == str(INFO.YES_NO)
        assert game.play("yes") == "You said yes."
        assert game.play("yes") == str(INFO.NOT_UNDERSTOOD)
        assert game.play("jump") == "Really?"
        assert game.play("no") == "You said no."
    
    def test_lock(self, game: Game):
        # move the player to the hidden place and try to go through the locked door
        game.state.player_location = game.state.rooms["hidden_place"]
        assert game.play("go west") == str(MOVING.FAIL_DOOR_LOCKED)
        assert game.play("open west") == str(ACTION.FAIL_NO_KEY)
        # give the key to the player
        game.state.inventory.add(game.state.rooms["marketplace"].items.pop("key"))
        assert game.play("open west") == str(ACTION.NOW_OPEN.format("open"))
        assert game.play("go west") == str(game.state.rooms["hidden_place2"].describe())
    
    def test_take(self, game: Game):
        assert game.state.inventory.items() == {}
        game.play("take diamond")
        assert "diamond" in game.state.inventory
    
    def test_score(self, game: Game):
        assert game.state.score == 0
        game.play("go north")
        assert game.state.score == game.state.player_location.value
        assert game.play("score") == str(INFO.SCORE.format(game.state.player_location.value))
    
    def test_hint(self, game: Game):
        warning, hint = game.state.player_location.get_hint()
        assert game.play("hint") == str(warning)
        assert game.play("no") == "ok."
        assert game.state.score == 0
        assert game.play("hint") == str(warning)
        assert game.play("yes") == str(hint)
        assert game.state.score == -game.state.player_location.hint_value
        game.state.player_location = game.state.rooms["field_1"]
        assert game.play("hint") == str(INFO.NO_HINT)


class TestHooks:

    def test_timehooks(self, game: Game):
        def time(state: State) -> m:
            state.time += 1
            return m()
        
        def daylight(state: State) -> m:
            if state.time >= 2:
                for room in state.rooms.values():
                    room.dark["now"] = True
            if state.time == 2:
                return m("The sun has set. It is dark now.")
        
        register_precommandhook("daylight", daylight)
        register_postcommandhook("time", time)
        assert game.state.time == 0
        game.play("go")
        assert game.state.time == 1
        game.play("go")
        assert game.play("look") == (
            "The sun has set. It is dark now.\nIt's pitch dark here. You can't see anything."
            " Anytime soon, you'll probably get attacked by some night creature."
        )
        assert game.state.time == 3
    
    def teardown_method(self, test_method):
        # unregister everything
        for hook in precommandhook_registry:
            unregister_precommandhook(hook)
        for hook in postcommandhook_registry:
            unregister_postcommandhook(hook)