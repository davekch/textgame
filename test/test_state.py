from unittest.mock import MagicMock
import pytest
from textgame.messages import m
from textgame.state import State, Event, Timer


@pytest.fixture
def state() -> State:
    player_location = MagicMock()
    return State(rooms={}, player_location=player_location)


class TestEvent:
    def test_timer(self, state: State):
        timer = Timer(time=state.time + 2, then=lambda _: m("quack"))
        state.set_event(timer)
        assert timer in state.events["pending"]
        assert state.pop_ready_events() == []
        # this should not have messed up anything
        assert timer in state.events["pending"]
        state.time += 2
        assert state.pop_ready_events() == [timer]
        assert state.events["pending"] == []
        assert state.events["ready"] == []
        assert timer.call(state) == m("quack")

    def test_event(self, state: State):
        event = Event(
            when=lambda s: s.player_location.id == "room0", then=lambda s: m("quack")
        )
        state.set_event(event)
        assert event in state.events["pending"]
        assert state.pop_ready_events() == []
        # this should not have messed up anything
        assert event in state.events["pending"]
        room0 = MagicMock()
        room0.id = "room0"
        state.player_location = room0
        assert state.pop_ready_events() == [event]
        assert state.events["pending"] == []
        assert state.events["ready"] == []
        assert event.call(state) == m("quack")

    def test_ready_timer(self, state: State):
        timer = Timer(time=0, then=MagicMock())
        state.set_event(timer)
        assert timer in state.events["ready"]
        assert state.pop_ready_events() == [timer]
        assert state.events["pending"] == []
        assert state.events["ready"] == []
