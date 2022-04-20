"""
textgame.parser
=================
"""

from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Generic, Optional, List, Dict, TypeVar
from abc import ABC, abstractmethod
from enum import Enum, auto
from .defaults import words


class Dictionary:
    """defines synonyms of words to be looked up by parsers"""

    words: Dict[str, str] = {}

    @classmethod
    def update_synonyms(cls, synonyms: Dict[str, List[str]]):
        """
        define synonyms for words

        :param synonym_dict: dict of the form ``{word: [synonyms], ...}``
        """
        for word, syns in synonyms.items():
            if type(syns) is not list:
                raise TypeError("synonyms must be defined as a list")
            for s in syns:
                cls.words[s] = word

    @classmethod
    def use_default_synonyms(cls):
        """populate the dictionary with a set of default vocabulary"""
        cls.update_synonyms(words.default_verb_synonyms)
        cls.update_synonyms(words.default_noun_synonyms)

    @classmethod
    def lookup(cls, word: str) -> str:
        if word not in cls.words:
            return word
        return cls.words[word]


ParsedType = TypeVar("ParsedType")


class Parser(ABC, Generic[ParsedType]):
    """Abstract base class for parsers"""

    @abstractmethod
    def parse_input(self, input: str) -> ParsedType:
        """take a string as input and parse it into something"""


@dataclass
class Command:
    """represents a parsed command"""

    verb: str
    noun: str


class YesNoAnswer(Enum):
    """represents a parsed answer to a yes/no question"""

    YES = auto()
    NO = auto()
    INVALID = auto()


class YesNoParser(Parser):
    """parser for answers to YesNoQuestions"""

    def parse_input(self, answer: str) -> YesNoAnswer:
        # improve this
        if Dictionary.lookup(answer) == words.YES:
            return YesNoAnswer.YES
        elif Dictionary.lookup(answer) == words.NO:
            return YesNoAnswer.NO
        else:
            return YesNoAnswer.INVALID


class MultipleChoiceParser(Parser):
    """parser for answers to MultipleChoiceQuestions"""

    def parse_input(self, input: str) -> str:
        return input.strip()


class CommandParser(Parser):
    """parser for commands that consist of two words (verb + noun)"""

    def parse_input(self, input: str) -> Optional[Command]:
        """
        take input and parse it into a Command
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
        # replace with the synonyms if there are some
        verb = Dictionary.lookup(verb)
        noun = Dictionary.lookup(noun)
        return Command(verb, noun)
