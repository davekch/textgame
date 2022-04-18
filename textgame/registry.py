from __future__ import annotations
from typing import (
    Callable,
    List,
    Optional,
    Union,
    TypeVar,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .messages import m
    from .state import State

    CommandArgTypes = TypeVar("CommandArgTypes")
    BehaviourArgTypes = TypeVar("BehaviourArgTypes")
    CommandFunc = Callable[[CommandArgTypes], m]
    BehaviourFunc = Callable[[BehaviourArgTypes], Optional[m]]
    HookFunc = Callable[[State], m]
    C = Union[CommandFunc, BehaviourFunc, HookFunc]


class Registry(dict):
    def register(self, name: str, func: C = None):
        if func is None:

            def decorator(_func):
                self[name] = _func
                return _func

            return decorator
        else:
            self[name] = func
            return func

    def unregister(self, name: str):
        self.pop(name, None)


command_registry: Registry[str, CommandFunc] = Registry()
behaviour_registry: Registry[str, BehaviourFunc] = Registry()
precommandhook_registry: Registry[str, HookFunc] = Registry()
postcommandhook_registry: Registry[str, HookFunc] = Registry()
roomhook_registry: Registry[str, HookFunc] = Registry()


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
