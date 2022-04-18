from textgame.defaults import hooks
from textgame.messages import m
from unittest.mock import MagicMock
import pytest


@pytest.fixture
def fake_creatures() -> MagicMock:
    creature_dict = {}
    for i in range(3):
        creature = MagicMock()
        creature.behaviours = {"mockbehaviour": {}}
        behaviourmethod = MagicMock()
        behaviourmethod.return_value = m()
        creature.call_behaviour = behaviourmethod
        creature_dict[f"creature_{i}"] = creature
    creatures = MagicMock()
    creatures.storage = creature_dict
    return creatures


@pytest.fixture
def fake_state(fake_creatures) -> MagicMock:
    state = MagicMock()
    state.creatures = fake_creatures
    return state


class TestHooks:
    def test_singlebehaviourhook(self, fake_state: MagicMock):
        mockhook = hooks.singlebehaviourhook("mockbehaviour")
        mockhook(fake_state)
        for creature in fake_state.creatures.storage.values():
            creature.call_behaviour.assert_called_once()