from __future__ import annotations
from enum import Enum, auto
from rich.console import Console
from .caller import Caller
from .state import PlayerStatus, State

import logging

logger = logging.getLogger("textgame.game")
logger.addHandler(logging.NullHandler())


class GameStatus(Enum):
    RUNNING = auto()
    OVER = auto()


class Game:
    def __init__(self, initial_state: State, caller: Caller):
        self.caller = caller
        self.state = initial_state
        self.status = GameStatus.RUNNING

    def play(self, input: str) -> str:
        """play one move of the game"""
        logger.debug(f"play move with the input {input!r}")
        msg = self.caller.call(input, self.state)
        logger.debug(f"finished the move with input {input!r}, response is {msg!r}")
        if self.state.player_status == PlayerStatus.DEAD:
            self.status = GameStatus.OVER
        return str(msg)

    def cli_loop(self, prompt: str = "> ", console: Console = None):
        if console:
            print = console.print
        while self.status == GameStatus.RUNNING:
            inp = input(prompt)
            response = self.play(inp)
            print(response)
            print()
