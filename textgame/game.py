from __future__ import annotations
from enum import Enum, auto
from .caller import SimpleCaller
from .parser import Parser
from .state import State

import logging
logger = logging.getLogger("textgame.game")
logger.addHandler(logging.NullHandler())


class GameStatus(Enum):
    RUNNING = auto()
    OVER = auto()


class Game:

    def __init__(self, initial_state: State, parser: Parser, caller_class=SimpleCaller):
        self.caller = caller_class()
        self.parser = parser
        self.state = initial_state
        self.status = GameStatus.RUNNING
    
    def play(self, input: str) -> str:
        """play one move of the game"""
        logger.debug(f"play move with the input {input!r}")
        parsed = self.parser.parse_input(input)
        logger.debug(f"input was parsed as {parsed!r}")
        msg = str(self.caller.call(parsed, self.state))
        logger.debug(f"finished the move with input {input!r}, response is {msg!r}")
        logger.debug(
            f"current state:\n"
            f"inventory: {self.state.inventory}\n"
            f"room's creatures: {self.state.player_location.creatures.keys()}\n"
            f"storate_room's creatures: {self.state.get_room('storage_room').creatures.keys()}\n"   # remove this soon
            f"time: {self.state.time}"
        )
        return str(msg)
    
    def cli_loop(self, prompt: str = "> "):
        while self.status == GameStatus.RUNNING:
            inp = input(prompt)
            response = self.play(inp)
            print(response)
            print()
