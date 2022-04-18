from typing import Callable
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
