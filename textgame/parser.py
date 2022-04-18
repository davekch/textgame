from dataclasses import dataclass
from typing import Protocol, Any
from enum import Enum, auto
from .defaults import words


class Parser(Protocol):

    def parse_command(self, input: str) -> Any:
        """take a string as input and parse it into something"""
        ...


@dataclass
class Command:
    verb: str
    noun: str


class YesNoAnswer(Enum):
    YES = auto()
    NO = auto()
    INVALID = auto()


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

    def parse_command(self, input: str) -> Command:
        """
        take input and return a Command
        """
        args = input.split()
        if len(args) > 2:
            raise ValueError()
        elif len(args) == 2:
            verb, noun = args
        elif len(args) == 1:
            verb = args[0]
            noun = ""
        else:
            verb = ""
            noun = ""
        return Command(verb, noun)