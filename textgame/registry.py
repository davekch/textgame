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

command_registry: Dict[str, Callable[[CommandArgTypes], m]] = {}
behaviour_registry: Dict[str, Callable[[BehaviourArgTypes], Optional[m]]] = {}
precommandhook_registry: OrderedDict[str, Callable[[State], m]] = OrderedDict()
postcommandhook_registry: OrderedDict[str, Callable[[State], m]] = OrderedDict()


def register_command(command: str):
    def decorated(func: Callable):
        command_registry[command] = func
        return func
    return decorated


def unregister_command(command: str):
    command_registry.pop(command, None)


def register_behaviour(name: str, func: Callable[[BehaviourArgTypes], Optional[m]] = None):
    if not func:
        # this means that this is called as a decorator @register_behaviour("behaviour")

        def decorator(_func: Callable[[BehaviourArgTypes], Optional[m]]):
            behaviour_registry[name] = _func
            return _func
        return decorator
    
    else:
        behaviour_registry[name] = func


def unregister_behaviour(name: str):
    behaviour_registry.pop(name, None)


def register_precommandhook(name: str, func: Callable[[State], m]):
    precommandhook_registry[name] = func


def unregister_precommandhook(name: str):
    precommandhook_registry.pop(name, None)


def register_postcommandhook(name: str, func: Callable[[State], m]):
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


def skip_precommandhook(func: Callable = None, skip: List[str] = None):
    return _skip_decoratorfactory("skip_precommandhook")(func, skip)


def get_precommandhook_skips(func: Callable) -> List[str]:
    if not hasattr(func, "skip_precommandhook"):
        return []
    if func.skip_precommandhook == "all":
        return list(precommandhook_registry.keys())
    else:
        return func.skip_precommandhook


def skip_postcommandhook(func: Callable = None, skip: List[str] = None):
    return _skip_decoratorfactory("skip_postcommandhook")(func, skip)


def get_postcommandhook_skips(func: Callable) -> List[str]:
    if not hasattr(func, "skip_postcommandhook"):
        return []
    if func.skip_postcommandhook == "all":
        return list(postcommandhook_registry.keys())
    else:
        return func.skip_postcommandhook
