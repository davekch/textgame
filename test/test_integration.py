from textgame.game import Game
from textgame.caller import SimpleCaller
from textgame.loader import StateBuilder
from textgame.state import Daytime, State
from textgame.messages import MultipleChoiceQuestion, YesNoQuestion, m
from textgame.room import Room
from textgame.state import State
from textgame.registry import (
    command_registry,
    precommandhook_registry,
    postcommandhook_registry,
    behaviour_registry,
    roomhook_registry,
)
from textgame.defaults import commands, behaviours, hooks
from textgame.defaults.words import ACTION, DESCRIPTIONS, MOVING, INFO
from textgame.things import Item, Monster, Weapon
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
def state(resources) -> State:
    commands.use_defaults()
    behaviour_registry.register("randomappearance", behaviours.RandomAppearance)
    behaviour_registry.register("randomwalk", behaviours.RandomWalk)
    behaviour_registry.register("random_spawn_once", behaviours.RandomSpawnOnce)
    behaviour_registry.register("fight", behaviours.Fight)
    return StateBuilder().build(initial_location="field_0", **resources)


@pytest.fixture
def game(state: State) -> Game:
    caller = SimpleCaller()
    return Game(initial_state=state, caller=caller)


class TestStateBuilder:
    """black box test for statebuilder"""

    def test_rooms_exist(self, state: State):
        assert "field_0" in state.rooms
        assert isinstance(state.get_room("field_0"), Room)

    def test_items_exist(self, state: State):
        assert "diamond" in state.things_manager.storage
        assert isinstance(state.things_manager.get("diamond"), Item)

    def test_items_in_room(self, state: State):
        assert "diamond" in state.get_room("field_0")


class TestGamePlay:
    def test_look(self, game: Game):
        expected = (
            str(game.state.rooms["field_0"].description)
            + "\n"
            + str(game.state.rooms["field_0"].things.get("diamond").description)
            + "\n"
            + str(game.state.rooms["field_0"].things.get("lamp").description)
        )
        assert game.play("look") == expected

    def test_darkness(self, game: Game):
        assert game.play("go east") == str(DESCRIPTIONS.DARK_L)
        game.state.inventory.add(game.state.things_manager.get("lamp"))
        assert game.play("look") == str(game.state.get_room("darkroom").description)
        # should also work if the lamp is in the room
        game.play("drop lamp")
        assert game.play("look") == str(
            game.state.get_room("darkroom").description
        ) + "\n" + str(game.state.things_manager.get("lamp").description)

    def test_custom_command(self, game: Game):
        @command_registry.register("scream")
        def scream(noun: str, state: State) -> m:
            return m(f"{noun.upper()}!!!")

        assert game.play("scream hello") == "HELLO!!!"

    def test_yesno(self, game: Game):
        @command_registry.register("jump")
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

    def test_nested_yesno(self, game: Game):
        @command_registry.register("jump")
        def jump(_noun: str, state: State):
            return YesNoQuestion(
                question="Do you really want to jump?",
                yes=YesNoQuestion(question="Really??", yes="ok, jump!", no="phew."),
                no="You said no.",
            )

        assert game.play("jump") == "Do you really want to jump?"
        assert game.play("no") == "You said no."
        game.play("jump")
        assert game.play("yes") == "Really??"
        assert game.play("no") == "phew."
        game.play("jump")
        game.play("yes")
        assert game.play("yes") == "ok, jump!"

    def test_multiplechoicequestion(self, game: Game):
        question = MultipleChoiceQuestion(
            question=m("What do you want to buy?"),
            answers={
                "bread": m("You buy bread."),
                "fish": lambda: m("You eat the fish."),  # test if callables also work
            },
        )

        @command_registry.register("trade")
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
        game.state.inventory.add(game.state.rooms["marketplace"].things.pop("key"))
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
        postcommandhook_registry.register("fight", hooks.singlebehaviourhook("fight"))
        goblin: Monster = game.state.things_manager.storage["goblin"]
        game.state.get_room("marketplace").things.add(goblin)
        response = game.play("go west")
        assert goblin.behaviours["fight"].fight_message in response
        assert game.state.health == 100 - goblin.strength
        response = game.play("fight goblin")
        assert str(ACTION.NO_WEAPONS) in response
        assert goblin.health == 100
        assert game.state.health == 50
        sword: Weapon = game.state.things_manager.storage["sword"]
        game.state.inventory.add(sword)
        response = game.play("fight goblin")
        assert "You use the sword against the mean goblin" in response
        assert goblin.behaviours["fight"].win_message in response
        assert not goblin.alive
        assert goblin.dead_description in game.play("look")

    def test_roomhook(self, game: Game):
        @roomhook_registry.register("field_1")
        def teleport_back(state: State):
            state.player_location = state.player_location_old
            return m("Some magic does not let you go there.")

        assert game.play(
            "go north"
        ) == "Some magic does not let you go there." + m.seperator + str(
            game.state.player_location.describe()
        )
        assert game.state.player_location.id == "field_0"

    def teardown_method(self, test_method):
        # unregister everything
        for hook in list(precommandhook_registry.keys()):
            precommandhook_registry.unregister(hook)
        for hook in list(postcommandhook_registry.keys()):
            postcommandhook_registry.unregister(hook)
        for behaviour in list(behaviour_registry.keys()):
            behaviour_registry.unregister(behaviour)
        for hook in list(roomhook_registry.keys()):
            roomhook_registry.unregister(hook)


class TestHooks:
    def test_timehooks(self, game: Game):
        precommandhook_registry.register(
            "daylight",
            hooks.daylight(
                duration_day=2, duration_night=3, on_sunset=lambda s: INFO.SUNSET
            ),
        )
        postcommandhook_registry.register("time", hooks.time)
        # first remove the lamp
        game.state.player_location.things.pop("lamp")
        assert game.state.time == 0
        game.play("go")
        assert game.state.time == 1
        game.play("go")
        assert game.play("look") == (
            "The sun has set. Night comes in.\nIt's pitch dark here. You can't see anything."
            " Anytime soon, you'll probably get attacked by some night creature."
        )
        assert game.state.time == 3

    def test_randomwalk_hook(self, game: Game):
        postcommandhook_registry.register("time", hooks.time)
        behaviour_registry.register("randomwalk", behaviours.RandomWalk)
        precommandhook_registry.register(
            "randomwalkhook", hooks.singlebehaviourhook("randomwalk")
        )
        randomwalker = game.state.things_manager.storage["randomwalker"]
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
            if randomnumber < randomwalker.behaviours["randomwalk"].mobility:
                assert game.state.get_location_of(randomwalker) == next(walk_iter)

    def test_randomspawn_hook(self, game: Game):
        behaviour_registry.register("random_spawn_once", behaviours.RandomSpawnOnce)
        precommandhook_registry.register(
            "spawn", hooks.singlebehaviourhook("random_spawn_once")
        )
        random = mock.MagicMock()
        random.random = yield_sequence(
            [0.8, 0.2]
        )  # first one doesn't trigger the spawn, second one does
        random.choice = lambda *args: "marketplace"
        game.state.random = random
        game.state.player_location = game.state.get_room("marketplace")
        game.play("look")
        # the creature randomspawner has the random_spawn_once behaviour
        assert "randomspawner" not in game.state.player_location.things
        game.play("look")
        assert "randomspawner" in game.state.player_location.things

    def test_daytime_hook(self, game: Game):
        precommandhook_registry.register(
            "daylight",
            hooks.daylight(
                duration_day=2,
                duration_night=3,
                on_sunset=lambda s: INFO.SUNSET,
                on_sunrise=lambda s: INFO.SUNRISE,
            ),
        )
        postcommandhook_registry.register("time", hooks.time)
        # first, remove the lightsource from the room
        game.state.player_location.things.pop("lamp")
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
            precommandhook_registry.unregister(hook)
        for hook in list(postcommandhook_registry.keys()):
            postcommandhook_registry.unregister(hook)
        for behaviour in list(behaviour_registry.keys()):
            behaviour_registry.unregister(behaviour)
