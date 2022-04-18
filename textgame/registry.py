from __future__ import annotations
from typing import (
    Callable,
    List,
    Type,
    TypeVar,
    Mapping,
    overload,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .messages import m, MessageType
    from .state import State
    from .things import Behaviour

    CommandFunc = Callable[[str, State], MessageType]
    BehaviourFunc = Type[Behaviour]
    HookFunc = Callable[[State], m]


C = TypeVar("C")


class Registry(dict, Mapping[str, C]):
    @overload
    def register(self, name: str) -> Callable[[C], C]:
        ...

    @overload
    def register(self, name: str, func: C) -> C:
        ...

    def register(self, name: str, func: C = None):
        def decorator(_func: C) -> C:
            self[name] = _func
            return _func

        if func is None:
            return decorator
        else:
            return decorator(func)

    def unregister(self, name: str):
        self.pop(name, None)


command_registry: Registry[CommandFunc] = Registry()
behaviour_registry: Registry[BehaviourFunc] = Registry()
precommandhook_registry: Registry[HookFunc] = Registry()
postcommandhook_registry: Registry[HookFunc] = Registry()
roomhook_registry: Registry[HookFunc] = Registry()


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
    skips = getattr(func, "skip_precommandhook", [])
    if skips == "all":
        return list(precommandhook_registry.keys())
    else:
        return skips


def skip_postcommandhook(func: CommandFunc = None, skip: List[str] = None):
    return _skip_decoratorfactory("skip_postcommandhook")(func, skip)


def get_postcommandhook_skips(func: CommandFunc) -> List[str]:
    skips = getattr(func, "skip_postcommandhook", [])
    if skips == "all":
        return list(postcommandhook_registry.keys())
    else:
        return skips
