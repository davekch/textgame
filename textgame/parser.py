from dataclasses import dataclass
from typing import Any, Optional, List, Dict
from abc import ABC, abstractmethod
from enum import Enum, auto
from .defaults import words


class Dictionary:
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
        cls.update_synonyms(words.default_verb_synonyms)
        cls.update_synonyms(words.default_noun_synonyms)

    @classmethod
    def lookup(cls, word: str) -> str:
        if word not in cls.words:
            return word
        return cls.words[word]


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


class YesNoParser(Parser):
    def parse_input(self, answer: str) -> YesNoAnswer:
        # improve this
        if Dictionary.lookup(answer) == words.YES:
            return YesNoAnswer.YES
        elif Dictionary.lookup(answer) == words.NO:
            return YesNoAnswer.NO
        else:
            return YesNoAnswer.INVALID


class MultipleChoiceParser(Parser):
    def parse_input(self, input: str) -> str:
        return input.strip()


class CommandParser(Parser):
    def parse_input(self, input: str) -> Optional[Command]:
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
        # replace with the synonyms if there are some
        verb = Dictionary.lookup(verb)
        noun = Dictionary.lookup(noun)
        return Command(verb, noun)
