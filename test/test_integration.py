from textgame.game import Game
from textgame.caller import SimpleCaller
from textgame.loader import StateBuilder
from textgame.state import Daytime, State
from textgame.messages import (
    ACTION,
    MOVING,
    MultipleChoiceQuestion,
    YesNoQuestion,
    m,
    INFO,
)
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
    behaviour_registry,
    register_behaviour,
    unregister_behaviour,
)
from textgame.defaults import commands, behaviours, hooks
from textgame.things import Monster, Weapon
from utils import yield_sequence
from typing import Dict
import json
import pytest
import os
from unittest import mock


BASEDIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def resources() -> Dict:
    with open(os.path.join(BASEDIR, "resources", "rooms.json")) as f:
        room_dicts = json.load(f)
    with open(os.path.join(BASEDIR, "resources", "items.json")) as f:
        item_dicts = json.load(f)
    with open(os.path.join(BASEDIR, "resources", "creatures.json")) as f:
        creature_dicts = json.load(f)
    return {
        "rooms": room_dicts,
        "items": item_dicts,
        "creatures": creature_dicts,
    }


@pytest.fixture
def game(resources) -> Game:
    register_behaviour("randomappearance", behaviours.RandomAppearance)
    register_behaviour("randomwalk", behaviours.RandomWalk)
    register_behaviour("random_spawn_once", behaviours.RandomSpawnOnce)
    state = StateBuilder().build(initial_location="field_0", **resources)
    caller = SimpleCaller()
    return Game(initial_state=state, caller=caller)


class TestGamePlay:
    def test_look(self, game: Game):
        expected = (
            str(game.state.rooms["field_0"].description)
            + "\n"
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
        def jump(_noun: str, state: State) -> YesNoQuestion:
            return YesNoQuestion(
                question=m("Really?"), yes=m("You said yes."), no=m("You said no.")
            )

        assert game.play("jump") == "Really?"
        assert game.play("go west") == str(INFO.YES_NO)
        assert game.play("yes") == "You said yes."
        assert game.play("yes") == str(INFO.NOT_UNDERSTOOD)
        assert game.play("jump") == "Really?"
        assert game.play("no") == "You said no."

    def test_multiplechoicequestion(self, game: Game):
        question = MultipleChoiceQuestion(
            question=m("What do you want to buy?"),
            answers={
                "bread": m("You buy bread."),
                "fish": lambda: m("You eat the fish."),  # test if callables also work
            },
        )

        @register_command("trade")
        def trade(noun: str, state: State) -> MultipleChoiceQuestion:
            return question

        assert game.play("trade") == (
            "What do you want to buy?\n (1) bread\n (2) fish\n (3) Cancel"
        )
        assert game.play("quack") == str(INFO.NO_VALID_ANSWER.format("1, 2, 3"))
        assert game.play("1") == "You buy bread."
        assert game.play("2") == str(INFO.NOT_UNDERSTOOD)
        game.play("trade")
        assert game.play("2") == "You eat the fish."

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
        assert game.play("score") == str(
            INFO.SCORE.format(game.state.player_location.value)
        )

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

    def test_fight(self, game: Game):
        register_postcommandhook("fight", hooks.manage_fights)
        goblin: Monster = game.state.creatures.storage["goblin"]
        game.state.get_room("marketplace").creatures.add(goblin)
        response = game.play("go west")
        assert goblin.fight_message in response
        assert game.state.health == 100 - goblin.strength
        response = game.play("fight goblin")
        assert str(ACTION.NO_WEAPONS) in response
        assert goblin.health == 100
        assert game.state.health == 50
        sword: Weapon = game.state.items.storage["sword"]
        game.state.inventory.add(sword)
        response = game.play("fight goblin")
        assert "You use the sword against the mean goblin" in response
        assert goblin.win_message in response
        assert not goblin.alive
        assert goblin.dead_description in game.play("look")


class TestHooks:
    def test_timehooks(self, game: Game):
        @register_precommandhook("daylight")
        def daylight(state: State) -> m:
            if state.time >= 2:
                for room in state.rooms.values():
                    room.dark["now"] = True
            if state.time == 2:
                return m("The sun has set. It is dark now.")

        register_postcommandhook("time", hooks.time)
        assert game.state.time == 0
        game.play("go")
        assert game.state.time == 1
        game.play("go")
        assert game.play("look") == (
            "The sun has set. It is dark now.\nIt's pitch dark here. You can't see anything."
            " Anytime soon, you'll probably get attacked by some night creature."
        )
        assert game.state.time == 3

    def test_randomwalk_hook(self, game: Game):
        register_postcommandhook("time", hooks.time)
        register_behaviour("randomwalk", behaviours.RandomWalk)
        register_precommandhook(
            "randomwalkhook", hooks.singlebehaviourhook("randomwalk")
        )
        randomwalker = game.state.creatures.storage["randomwalker"]
        randomwalker_location = game.state.get_location_of(randomwalker)
        assert randomwalker_location == game.state.get_room("marketplace")

        # define a sequence of rooms where the randomwalker walks
        walk = [
            game.state.get_room("field_0"),
            game.state.get_room("field_1"),
            game.state.get_room("field_0"),
        ]
        randomnumbers = [0.2, 0.7, 0.2, 0.6, 0.6, 0.4]
        # monkeypatch the random engine
        random = mock.MagicMock()
        random.choice = yield_sequence(walk)
        random.random = yield_sequence(randomnumbers)
        game.state.random = random

        walk_iter = iter(walk)
        for randomnumber in randomnumbers:
            game.play("look")
            if randomnumber < randomwalker.behaviours["randomwalk"].params["mobility"]:
                assert game.state.get_location_of(randomwalker) == next(walk_iter)

    def test_randomspawn_hook(self, game: Game):
        register_behaviour("random_spawn_once", behaviours.RandomSpawnOnce)
        register_precommandhook("spawn", hooks.singlebehaviourhook("random_spawn_once"))
        random = mock.MagicMock()
        random.random = yield_sequence(
            [0.8, 0.2]
        )  # first one doesn't trigger the spawn, second one does
        random.choice = lambda *args: "marketplace"
        game.state.random = random
        game.state.player_location = game.state.get_room("marketplace")
        game.play("look")
        # the creature randomspawner has the random_spawn_once behaviour
        assert "randomspawner" not in game.state.player_location.creatures
        game.play("look")
        assert "randomspawner" in game.state.player_location.creatures

    def test_daytime_hook(self, game: Game):
        register_precommandhook(
            "daylight", hooks.daylight(duration_day=2, duration_night=3)
        )
        register_postcommandhook("time", hooks.time)
        for _ in range(2):
            response = game.play("look")
            assert (
                str(INFO.SUNSET) not in response and str(INFO.SUNRISE) not in response
            )
        assert game.state.time == 2
        assert str(INFO.SUNSET) in game.play("look")
        assert game.state.daytime == Daytime.NIGHT
        assert game.state.player_location.is_dark()
        for _ in range(2):
            response = game.play("look")
            assert (
                str(INFO.SUNSET) not in response and str(INFO.SUNRISE) not in response
            )
        assert game.state.time == 5
        assert str(INFO.SUNRISE) in game.play("look")
        assert game.state.daytime == Daytime.DAY
        assert not game.state.player_location.is_dark()

    def teardown_method(self, test_method):
        # unregister everything
        for hook in list(precommandhook_registry.keys()):
            unregister_precommandhook(hook)
        for hook in list(postcommandhook_registry.keys()):
            unregister_postcommandhook(hook)
        for behaviour in list(behaviour_registry.keys()):
            unregister_behaviour(behaviour)
