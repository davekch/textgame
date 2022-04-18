from __future__ import annotations
from enum import Enum, auto
from typing import Union, Callable
from .caller import SimpleCaller
from .parser import SimpleParser, YesNoAnswer
from .state import State
from .messages import m, INFO

import logging
logger = logging.getLogger("textgame.game")
logger.addHandler(logging.NullHandler())


class GameStatus(Enum):
    RUNNING = auto()
    OVER = auto()


class Game:

    def __init__(self, initial_state: State, caller_class=SimpleCaller, parser_class=SimpleParser):
        self.caller = caller_class()
        self.parser = parser_class()
        self.state = initial_state
        self.status = GameStatus.RUNNING
    
    def play(self, input: str) -> str:
        """play one move of the game"""
        logger.debug(f"play move with the input {input!r}")
        parsed = self.parser.parse_input(input)
        logger.debug(f"input was parsed as {parsed!r}")
        msg = str(self.caller.call(parsed, self.state))
        logger.debug(f"finished the move with input {input!r}, response is {msg!r}")
        return str(msg)
    
    def cli_loop(self, prompt: str = "> "):
        while self.status == GameStatus.RUNNING:
            inp = input(prompt)
            response = self.play(inp)
            print(response)
            print()
