from __future__ import annotations
from enum import Enum, auto
from typing import Union, Callable
from .caller import SimpleCaller
from .parser import SimpleParser, YesNoAnswer
from .state import State
from .messages import m, INFO

import logging
logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())


class GameStatus(Enum):
    RUNNING = auto()
    OVER = auto()
    YESNOLOOP = auto()


class Game:

    def __init__(self, initial_state: State, caller_class=SimpleCaller, parser_class=SimpleParser):
        self.caller = caller_class()
        self.parser = parser_class()
        self.state = initial_state
        self.status = GameStatus.RUNNING
        self.modes = {
            GameStatus.RUNNING: Game.play_normal_mode,
            GameStatus.YESNOLOOP: Game.play_yesno_loop,
        }
    
    def define_mode(self, status: GameStatus, function: Callable[[Game, str], m]):
        self.mode[status] = function
    
    def play_normal_mode(self, input: str) -> m:
        """play one move of the game"""
        logger.debug(f"execute normal mode with input {input!r}")
        try:
            command = self.parser.parse_command(input)
        except ValueError:
            return INFO.TOO_MANY_ARGUMENTS

        msg = self.caller.call_with_hooks(command, self.state)
        if msg.needs_answer:   # if the message is a question
            self.status = GameStatus.YESNOLOOP
        return msg

    def play_yesno_loop(self, input: str) -> m:
        logger.debug(f"execute yesno mode with input {input!r}")
        answer = self.parser.parse_yesno(input)
        if answer == YesNoAnswer.INVALID:
            msg = INFO.YES_NO
        else:
            self.status = GameStatus.RUNNING
            msg = self.caller.call_yesno(answer)
        return msg
    
    def play_as_it_should_be(self, input: str) -> str:
        # make it work!
        # ideas: place all info in Command, ie is_valid, yesno
        command = self.parser.parse_command(input)
        return self.caller.call_command(command, self.state)
    
    def play(self, input: str) -> str:
        logger.debug(f"play move with the input {input!r}")
        msg = m()
        for status, mode in self.modes.items():
            if self.status == status:
                logger.debug(f"game in status {self.status}, execute corresponding mode")
                msg += mode(self, input)
                break
                
        logger.debug(f"finished the move with input {input!r}, response is {msg!r}")
        return str(msg)
    
    def cli_loop(self, prompt: str = "> "):
        while self.status == GameStatus.RUNNING:
            inp = input(prompt)
            response = self.play(inp)
            print(response)
            print()
