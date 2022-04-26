"""
textgame.registry
===================

This module contains a couple of global ``Registry`` objects.

 - ``command_registry: Registry[Callable[[str, State], MessageProtocol]]``: mapping of commands to
   functions that should be called when the user uses the command, eg 'go' -> <function go>
 - ``behaviour_registry: Registry[Type[Behaviour]]``: mapping of names to behavior classes
 - ``precommandhook_registry: Registry[Callable[[State], m]]``: mapping of names to functions that
   should be called before each command
 - ``postcommandhook_registry: Registry[Callable[[State], m]]``: mapping of names to functions that
   should be called after each command
 - ``roomhook_registry: Registry[Callable[[State], m]]``: mapping of room-ids to functions that should
   be called when the player enters the room

To register a given function / class to a registry, use the registry's ``register`` method either as
a standard function call or as a decorator:

.. code-block:: python

    @command_registry.register("go")
    def go(direction: str, state: State) -> m:
        ...
    
    def update_daytime(state: State) -> m:
        ...
    
    postcommandhook_registry.register("daytime", update_daytime)
"""


from __future__ import annotations
from typing import (
    Callable,
    List,
    Type,
    TypeVar,
    Mapping,
    overload,
)
from ._util import obj_info

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .messages import m, MessageProtocol
    from .state import State
    from .things import Behaviour

    CommandFunc = Callable[[str, State], MessageProtocol]
    BehaviourFunc = Type[Behaviour]
    HookFunc = Callable[[State], m]


C = TypeVar("C")


class Registry(dict, Mapping[str, C]):
    """mapping of strings to objects.
    The main use of this class is its register method which can be used
    as a decorator.
    """

    @overload
    def register(self, name: str) -> Callable[[C], C]:
        ...

    @overload
    def register(self, name: str, func: C) -> C:
        ...

    def register(self, name: str, func: C = None):
        """
        store ``func`` under the key ``name``.
        this method may be used in two different ways:
        
        as a regular function:

        .. code-block:: python
    
            registry: Registry[Callable] = Registry()
            registry.register(name, func)
        
        or as a decorator:

        .. code-block:: python

            @registry.register(name)
            def func(): ...
        """

        def decorator(_func: C) -> C:
            self[name] = _func
            return _func

        if func is None:
            return decorator
        else:
            return decorator(func)

    def unregister(self, name: str):
        """pop ``name`` from self"""
        self.pop(name, None)

    def __repr__(self) -> str:
        description_dict = {key: obj_info(value) for key, value in self.items()}
        return repr(description_dict)


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
    """mark a command-function so that the passed precommandhooks are
    not called prior this function.
    can be used as a decorator like this:

    .. code-block:: python

        @skip_precommandhook(["daylight"])
        @command_registry.register("command1")
        def mycommand1(noun: str, state: State) -> m:
            '''when this command is called, the precommandhook "daylight" is skipped'''

        @skip_precommandhook
        @command_registry.register("command2")
        def mycommand2(noun: str, state: State) -> m:
            '''when this command is called, all precommandhooks are skipped'''
    """
    return _skip_decoratorfactory("skip_precommandhook")(func, skip)


def get_precommandhook_skips(func: CommandFunc) -> List[str]:
    """get the names of precommandhooks that should not be called before ``func``"""
    skips = getattr(func, "skip_precommandhook", [])
    if skips == "all":
        return list(precommandhook_registry.keys())
    else:
        return skips


def skip_postcommandhook(func: CommandFunc = None, skip: List[str] = None):
    """same as :func:`skip_precommandhook` but for postcommandhook"""
    return _skip_decoratorfactory("skip_postcommandhook")(func, skip)


def get_postcommandhook_skips(func: CommandFunc) -> List[str]:
    """get the names of postcommandhooks that should not be called after ``func``"""
    skips = getattr(func, "skip_postcommandhook", [])
    if skips == "all":
        return list(postcommandhook_registry.keys())
    else:
        return skips
