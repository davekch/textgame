from dataclasses import dataclass
from typing import Any, Union, Optional, List, Dict
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

    def __init__(self, verb_synonyms: Dict[str, List[str]] = None, noun_synonyms: Dict[str, List[str]] = None):
        self.verb_synonyms: Dict[str, str] = {}
        self.noun_synonyms: Dict[str, str] = {}
        if verb_synonyms:
            self.update_verb_synonyms(verb_synonyms)
        if noun_synonyms:
            self.update_verb_synonyms(noun_synonyms)
        
    def update_verb_synonyms(self, synonyms: Dict[str, List[str]]):
        """
        define synonyms for verbs

        :param synonym_dict: dict of the form ``{command: [synonyms], ...}``
        """
        for command, synonyms in synonyms.items():
            if type(synonyms) is not list:
                raise TypeError("synonyms must be defined as a list")
            for s in synonyms:
                self.verb_synonyms[s] = command
        
    def update_noun_synonyms(self, synonyms: Dict[str, List[str]]):
        """
        define synonyms for verbs

        :param synonym_dict: dict of the form ``{command: [synonyms], ...}``
        """
        for noun, synonyms in synonyms.items():
            if type(synonyms) is not list:
                raise TypeError("synonyms must be defined as a list")
            for s in synonyms:
                self.noun_synonyms[s] = noun
            
    def use_default_synonyms(self):
        self.update_verb_synonyms(words.default_verb_synonyms)
        self.update_noun_synonyms(words.default_noun_synonyms)

    def lookup_verb(self, verb: str) -> str:
        return self.verb_synonyms.get(verb) or verb

    def lookup_noun(self, noun: str) -> str:
        return self.noun_synonyms.get(noun) or noun
    
    def parse_yesno(self, answer: str) -> YesNoAnswer:
        if self.lookup_noun(answer) == words.YES:
            return YesNoAnswer.YES
        elif self.lookup_noun(answer) == words.NO:
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
        # replace with the synonyms if there are some
        verb = self.lookup_verb(verb)
        noun = self.lookup_noun(noun)
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

