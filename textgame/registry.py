from __future__ import annotations
from functools import wraps
from typing import Callable, Dict, List, Optional, Union, TypeVar, OrderedDict
from collections import OrderedDict

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .messages import m
    from .state import State

    CommandArgTypes = TypeVar("CommandArgTypes")
    BehaviourArgTypes = TypeVar("BehaviourArgTypes")
    CommandFunc = Callable[[CommandArgTypes], m]
    BehaviourFunc = Callable[[BehaviourArgTypes], Optional[m]]
    HookFunc = Callable[[State], m]


command_registry: Dict[str, CommandFunc] = {}
behaviour_registry: Dict[str, BehaviourFunc] = {}
precommandhook_registry: OrderedDict[str, HookFunc] = OrderedDict()
postcommandhook_registry: OrderedDict[str, HookFunc] = OrderedDict()


def register_command(command: str) -> Callable[[CommandFunc], CommandFunc]:
    def decorated(func: CommandFunc) -> CommandFunc:
        command_registry[command] = func
        return func
    return decorated


def unregister_command(command: str):
    command_registry.pop(command, None)


def register_behaviour(name: str, func: BehaviourFunc = None):
    if not func:
        # this means that this is called as a decorator @register_behaviour("behaviour")

        def decorator(_func: BehaviourFunc) -> BehaviourFunc:
            behaviour_registry[name] = _func
            return _func
        return decorator
    
    else:
        behaviour_registry[name] = func


def unregister_behaviour(name: str):
    behaviour_registry.pop(name, None)


def register_precommandhook(name: str, func: HookFunc):
    precommandhook_registry[name] = func


def unregister_precommandhook(name: str):
    precommandhook_registry.pop(name, None)


def register_postcommandhook(name: str, func: HookFunc):
    postcommandhook_registry[name] = func


def unregister_postcommandhook(name: str):
    postcommandhook_registry.pop(name, None)


def _skip_decoratorfactory(flag: str):

    def skip_decorator(func: Callable = None, skip: List[str] = None):
        # hack to make all of these work: @skip_decorator, @skip_decorator([...])
        if isinstance(func, list):
            skip = func
            func = None
        if not func and skip:
            def decorator(_func):
                setattr(_func, flag, skip)
                return _func
            return decorator
        else:
            setattr(func, flag, "all")
            return func
        
    return skip_decorator


def skip_precommandhook(func: CommandFunc = None, skip: List[str] = None):
    return _skip_decoratorfactory("skip_precommandhook")(func, skip)


def get_precommandhook_skips(func: CommandFunc) -> List[str]:
    if not hasattr(func, "skip_precommandhook"):
        return []
    if func.skip_precommandhook == "all":
        return list(precommandhook_registry.keys())
    else:
        return func.skip_precommandhook


def skip_postcommandhook(func: CommandFunc = None, skip: List[str] = None):
    return _skip_decoratorfactory("skip_postcommandhook")(func, skip)


def get_postcommandhook_skips(func: CommandFunc) -> List[str]:
    if not hasattr(func, "skip_postcommandhook"):
        return []
    if func.skip_postcommandhook == "all":
        return list(postcommandhook_registry.keys())
    else:
        return func.skip_postcommandhook
