from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Type, TypeVar, Callable, List, Any
from abc import ABC, abstractmethod
from .parser import (
    Parser,
    CommandParser,
    YesNoAnswer,
    Command,
    YesNoParser,
    MultipleChoiceParser,
)
from .state import State
from .messages import MessageType, MultipleChoiceQuestion, m, YesNoQuestion, INFO
from .registry import (
    command_registry,
    precommandhook_registry,
    postcommandhook_registry,
    get_precommandhook_skips,
    get_postcommandhook_skips,
)
from .exceptions import ModeNotFoundError

import logging

logger = logging.getLogger("textgame.caller")
logger.addHandler(logging.NullHandler())


@dataclass
class Response:
    # the response type is there to communicate between interpreters and callers
    # the interpreters get messages and wrap them in a response, setting a type
    # so that the caller can check the type and set its mode accordingly.
    # case where this is really necessary: when a response is preehookmsg + enteryesnoloop + posthookmsg
    value: MessageType | List[MessageType]
    type: Type[MessageType] = None

    def __post_init__(self):
        if not self.type:
            self.type = type(self.value)

    def to_message(self):
        if isinstance(self.value, list):
            msg = m()
            for v in self.value:
                msg += v.to_message()
            return msg
        return self.value


class Interpreter(ABC):
    ParsedInputType = TypeVar("ParsedInputType")
    StateType = TypeVar("StateType")

    def __init__(self):
        self.previous_result: Response = None
        self.success: bool = True  # should be set by self.interpret

    def backup_result(self, result):
        self.previous_result = result

    @abstractmethod
    def interpret(self, input: ParsedInputType, state: StateType) -> Response:
        """get and call the function corresponding to the parsed command"""
        pass


class CommandInterpreter(Interpreter):
    def interpret(self, input: Command, state: State) -> Response:
        logger.debug(f"got {input!r} as command")
        return self.call_with_hooks(input, state)

    def call_command(self, command: Command, state: State) -> Any:
        """get the function corresponding to the command and call it"""
        try:
            func = self.get_function(command)
            result = self.call_function(func, command, state)
            self.success = True
        except KeyError:
            result = INFO.NOT_UNDERSTOOD
            self.success = False
        return result

    def call_with_hooks(self, command: Command, state: State) -> Response:
        try:
            self.success = True
            func = self.get_function(command)
        except KeyError:
            self.success = False
            return Response(INFO.NOT_UNDERSTOOD)

        prehookmsg = call_precommandhook(state, skip=get_precommandhook_skips(func))
        commandresponse = self.call_function(func, command, state)
        posthookmsg = call_postcommandhook(state, skip=get_postcommandhook_skips(func))
        return Response(
            value=[prehookmsg, commandresponse, posthookmsg], type=type(commandresponse)
        )

    def call_function(
        self, function: Callable[..., m], command: Command, state: State
    ) -> m:
        """define how a function should be called given the state and parsed command"""
        logger.debug(f"calling {function}")
        result = function(command.noun, state)
        # convert result to m if it is a string
        if isinstance(result, str):
            result = m(result)
        return result

    def get_function(self, command: Command) -> Callable[[str, State], m]:
        if command.verb not in command_registry:
            logger.debug(f"could not find function for verb {command.verb!r}")
            raise KeyError
        logger.debug(f"got function {command_registry[command.verb]}")
        return command_registry[command.verb]


class YesNoInterpreter(Interpreter):
    def interpret(self, answer: YesNoAnswer, _state: State) -> Response:
        logger.debug(f"got answer {answer!r}")
        self.success = True
        # if the previous result was multiple messages, get the question first
        if isinstance(self.previous_result.value, list):
            for msg in self.previous_result.value:
                if isinstance(msg, YesNoQuestion):
                    question = msg
                    break
        else:
            question = self.previous_result.value
        if answer == YesNoAnswer.YES:
            result = question.yes()
        elif answer == YesNoAnswer.NO:
            result = question.no()
        else:
            self.success = False
            return Response(INFO.YES_NO)
        return Response(result)


class MultipleChoiceInterpreter(Interpreter):
    def interpret(self, answer: str, state: State) -> Response:
        logger.debug(f"got answer {answer!r}")
        # if the previous result was multiple messages, get the question first
        if isinstance(self.previous_result.value, list):
            for msg in self.previous_result.value:
                if isinstance(msg, MultipleChoiceQuestion):
                    question = msg
                    break
        else:
            question = self.previous_result.value
        if not answer in question.possible_answers:
            self.success = False
            return Response(
                INFO.NO_VALID_ANSWER.format(", ".join(question.possible_answers))
            )
        self.success = True
        return Response(question.get_response(answer))


class Caller(ABC):
    StateType = TypeVar("StateType")

    @abstractmethod
    def call(self, input: str, state: StateType) -> MessageType:
        """parse input and call the function corresponding to the parsed input"""
        pass


class CallerMode(Enum):
    NORMAL = auto()
    YESNO = auto()
    MULTIPLECHOICE = auto()


class SimpleCaller(Caller):
    def __init__(self):
        self.mode = CallerMode.NORMAL
        modes = {
            CallerMode.NORMAL: (CommandParser, CommandInterpreter),
            CallerMode.YESNO: (YesNoParser, YesNoInterpreter),
            CallerMode.MULTIPLECHOICE: (
                MultipleChoiceParser,
                MultipleChoiceInterpreter,
            ),
        }
        self.mode_switches = {
            m: CallerMode.NORMAL,
            YesNoQuestion: CallerMode.YESNO,
            MultipleChoiceQuestion: CallerMode.MULTIPLECHOICE,
        }
        # initialize interpreters and parsers
        self.parsers: Dict[CallerMode, Parser] = {m: p() for m, (p, _) in modes.items()}
        self.interpreters: Dict[CallerMode, Interpreter] = {
            m: i() for m, (_, i) in modes.items()
        }

    def set_mode(
        self,
        mode: CallerMode,
        parser_class: Type[Parser],
        interpreter_class: Type[Interpreter],
        switch_type: Type,
    ):
        self.parsers[mode] = parser_class()
        self.interpreters[mode] = interpreter_class()
        self.mode_switches[switch_type] = mode

    def call(self, input: str, state: State) -> m:
        logger.debug(f"process input {input!r}")
        parsed = self.parsers[self.mode].parse_input(input)
        result = self.interpreters[self.mode].interpret(parsed, state)
        logger.debug(f"got result {result!r}")
        # check in which mode we should switch
        self.check_result(result)
        return result.to_message()

    def check_result(self, result: Response) -> m:
        if result.type not in self.mode_switches:
            raise ModeNotFoundError(
                f"response contains unexpected type: {result.type!r}. no mode is configured for this type"
            )
        # only switch if the current interpreter is done
        if self.interpreters[self.mode].success:
            self.mode = self.mode_switches[result.type]
            logger.debug(
                f"result was of type {result.type} and successful, going into mode {self.mode!r}"
            )
            # backup the result for the coming parser
            next_interpreter = self.interpreters[self.mode]
            next_interpreter.backup_result(result)
        else:
            logger.debug(
                f"the interpreter {self.interpreters[self.mode]} reported no success, staying in mode {self.mode!r}"
            )


def call_precommandhook(state: State, skip: List[str] = None) -> m:
    msg = m()
    for name, func in precommandhook_registry.items():
        if name not in (skip or []):
            logger.debug(f"call precommandhook {func!r}")
            msg += func(state)
    return msg


def call_postcommandhook(state: State, skip: List[str] = None) -> m:
    msg = m()
    for name, func in postcommandhook_registry.items():
        if name not in (skip or []):
            logger.debug(f"call postcommandhook {func!r}")
            msg += func(state)
    return msg
