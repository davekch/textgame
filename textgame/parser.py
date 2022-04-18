from dataclasses import dataclass
from typing import Any, Union, Optional
from abc import ABC, abstractmethod
from enum import Enum, auto
from .defaults import words


class Parser(ABC):

    @abstractmethod
    def parse_input(self, input: str) -> Any:
        """take a string as input and parse it into something"""
        pass


@dataclass
class Command:
    verb: str
    noun: str


class YesNoAnswer(Enum):
    YES = auto()
    NO = auto()
    INVALID = auto()


@dataclass
class ParsedInput:

    type: Union[Command, YesNoAnswer, None]
    value: Union[Command, YesNoAnswer] = None

    def is_valid(self) -> bool:
        return self.type is not None
    
    def get(self) -> Union[Command, YesNoAnswer]:
        return self.value


class SimpleParser(Parser):

    def lookup_verb(self, verb: str) -> str:
        return verb
    
    def lookup_noun(self, noun: str) -> str:
        return noun
    
    def parse_yesno(self, answer: str) -> YesNoAnswer:
        if answer == words.YES:
            return YesNoAnswer.YES
        elif answer == words.NO:
            return YesNoAnswer.NO
        else:
            return YesNoAnswer.INVALID

    def parse_command(self, input: str) -> Optional[Command]:
        """
        take input and return a Command
        """
        args = input.split()
        if len(args) > 2:
            return None
        elif len(args) == 2:
            verb, noun = args
        elif len(args) == 1:
            verb = args[0]
            noun = ""
        else:
            verb = ""
            noun = ""
        return Command(verb, noun)
    
    def parse_input(self, input: str) -> ParsedInput:
        # try to parse the input as a yesno answer, if that fails, try to parse a command
        yesno_parsed = self.parse_yesno(input)
        if yesno_parsed != YesNoAnswer.INVALID:
            return ParsedInput(type=YesNoAnswer, value=yesno_parsed)
        command_parsed = self.parse_command(input)
        if command_parsed:
            return ParsedInput(type=Command, value=command_parsed)
        return ParsedInput(type=None)

