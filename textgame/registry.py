from functools import wraps
from typing import Callable, List
from collections import OrderedDict


command_registry = {}
precommandhook_registry = OrderedDict()
postcommandhook_registry = OrderedDict()



def register_command(command: str):
    def decorated(func: Callable):
        command_registry[command] = func
        return func
    return decorated


def register_precommandhook(name: str, func: Callable):
    precommandhook_registry[name] = func


def register_postcommandhook(name: str, func: Callable):
    postcommandhook_registry[name] = func


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
