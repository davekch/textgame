from typing import TypeVar, Union, Callable, List, Protocol, Any
from .parser import Command, YesNoAnswer
from .state import State
from .messages import m, EnterYesNoLoop, INFO
from .registry import command_registry, precommandhook_registry, postcommandhook_registry

import logging
logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())


class Caller(Protocol):

    MessageType = TypeVar("MessageType")
    CommandType = TypeVar("CommandType")
    StateType = TypeVar("StateType")

    def call(
        self,
        function: Callable[..., MessageType],
        command: CommandType,
        state: StateType
    ) -> MessageType:
        """define how a function should be called given the state and parsed command"""
        ...
    
    def get_function(self, command: CommandType) -> Callable[..., MessageType]:
        """define how a function is selected given the parsed command"""
        ...
    
    def call_command(self, command: CommandType, state: StateType) -> MessageType:
        """get and call the function corresponding to the parsed command"""
        ...



class SimpleCaller(Caller):

    def __init__(self):
        # when the result of a command call is an EnterYesNoLoop, backup the functions
        # that should be run when the next answer is yes or no
        self.yesno_backup: EnterYesNoLoop = None
    
    def call(self, function: Callable[..., m], command: Command, state: State) -> m:
        """define how a function should be called given the state and parsed command"""
        return function(command.noun, state)
    
    def get_function(self, command: Command) -> Callable[[str, State], m]:
        if command.verb not in command_registry:
            raise KeyError
        return command_registry[command.verb]

    def call_command(self, command: Command, state: State) -> m:
        try:
            func = self.get_function(command)
            result = self.call(func, command, state)
        except KeyError:
            result = INFO.NOT_UNDERSTOOD
        return self.check_result(result)
    
    def check_result(self, result: Union[m, EnterYesNoLoop]) -> m:
        if isinstance(result, EnterYesNoLoop):
            logger.debug("got EnterYesNoLoop as response, return message with needs_answer=True")
            self.yesno_backup = result
            return m(result.question, needs_answer=True)
        return result
    
    def call_with_hooks(self, command: Command, state: State) -> m:
        try:
            func = command_registry[command.verb]
        except KeyError:
            return INFO.NOT_UNDERSTOOD
        
        if not getattr(func, "skip_all_precommandhooks", False):
            skip = getattr(func, "skip_precommandhooks", [])
            prehookmsg = self.call_precommandhook(state, skip=skip)
        else:
            prehookmsg = m()
        commandresponse = self.call_command(command, state)
        if not getattr(func, "skip_all_postcommandhooks", False):
            skip = getattr(func, "skip_postcommandhooks", [])
            posthookmsg = self.call_postcommandhook(state, skip=skip)
        else:
            posthookmsg = m()
        return prehookmsg + commandresponse + posthookmsg
    
    def call_yesno(self, answer: YesNoAnswer) -> m:
        logger.debug(f"caller in yesno-mode, got answer {answer}")
        if answer == YesNoAnswer.YES:
            result = self.yesno_backup.yes()
        elif answer == YesNoAnswer.NO:
            result = self.yesno_backup.no()
        else:
            raise ValueError("caller received invalid YesNoAnswer")
        self.yesno_backup = None
        return self.check_result(result)
    
    def call_precommandhook(self, state: State, skip: List[str] = None) -> m:
        msg = m()
        for name, func in precommandhook_registry.items():
            if name not in (skip or []):
                msg += func(state)
        return msg
    
    def call_postcommandhook(self, state: State, skip: List[str] = None) -> m:
        msg = m()
        for name, func in postcommandhook_registry.items():
            if name not in (skip or []):
                msg += func(state)
        return msg
