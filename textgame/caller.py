from typing import TypeVar, Union, Callable, List, Any
from abc import ABC, abstractmethod
from .parser import ParsedInput, YesNoAnswer, Command
from .state import State
from .messages import m, EnterYesNoLoop, INFO
from .registry import (
    command_registry,
    precommandhook_registry,
    postcommandhook_registry,
    get_precommandhook_skips,
    get_postcommandhook_skips,
)

import logging

logger = logging.getLogger("textgame.caller")
logger.addHandler(logging.NullHandler())


class Caller(ABC):

    MessageType = TypeVar("MessageType")
    ParsedInputType = TypeVar("ParsedInputType")
    StateType = TypeVar("StateType")

    @abstractmethod
    def call(self, input: ParsedInputType, state: StateType) -> MessageType:
        """get and call the function corresponding to the parsed command"""
        pass


class SimpleCaller(Caller):
    def __init__(self):
        # when the result of a command call is an EnterYesNoLoop, backup the functions
        # that should be run when the next answer is yes or no and go into yesno-loop
        self.in_yesno_loop: bool = False
        self.yesno_backup: EnterYesNoLoop = None

    def call_function(
        self, function: Callable[..., m], command: Command, state: State
    ) -> m:
        """define how a function should be called given the state and parsed command"""
        return function(command.noun, state)

    def get_function(self, command: Command) -> Callable[[str, State], m]:
        if command.verb not in command_registry:
            raise KeyError
        return command_registry[command.verb]

    def call(self, input: ParsedInput, state: State) -> m:
        if self.in_yesno_loop:
            logger.debug(
                f"in yesno-loop, going to call the yesno function for the question {self.yesno_backup.question!r}"
            )
            return self.call_yesno(input.get())
        else:
            logger.debug(f"normal mode, going to call with hooks")
            if input.type != Command:
                return INFO.NOT_UNDERSTOOD
            return self.call_with_hooks(input.get(), state)

    def call_command(self, command: Command, state: State) -> m:
        """get the function corresponding to the command and call it"""
        try:
            func = self.get_function(command)
            result = self.call_function(func, command, state)
        except KeyError:
            result = INFO.NOT_UNDERSTOOD
        return self.check_result(result)

    def check_result(self, result: Union[m, EnterYesNoLoop]) -> m:
        """see if the result of a function call is a message or EnterYesNoLoop and extract the latter, returning a message in any case"""
        if isinstance(result, EnterYesNoLoop):
            logger.debug("got EnterYesNoLoop as response, go into in_yesno_loop mode")
            self.in_yesno_loop = True
            self.yesno_backup = result
            return m(result.question)

        # in any other case, we're in normal mode
        self.in_yesno_loop = False
        self.yesno_backup = None
        return result

    def call_with_hooks(self, command: Command, state: State) -> m:
        logger.debug(f"got {command} as command")
        try:
            func = command_registry[command.verb]
        except KeyError:
            return INFO.NOT_UNDERSTOOD

        prehookmsg = call_precommandhook(state, skip=get_precommandhook_skips(func))
        commandresponse = self.call_command(command, state)
        posthookmsg = call_postcommandhook(state, skip=get_postcommandhook_skips(func))
        return prehookmsg + commandresponse + posthookmsg

    def call_yesno(self, answer: YesNoAnswer) -> m:
        logger.debug(f"caller in yesno-mode, got answer {answer}")
        if answer == YesNoAnswer.YES:
            result = self.yesno_backup.yes()
        elif answer == YesNoAnswer.NO:
            result = self.yesno_backup.no()
        else:
            return INFO.YES_NO
        return self.check_result(result)


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
