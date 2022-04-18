from typing import Any
import os
import inspect


def obj_info(obj: Any) -> str:
    """get repr and file of obj"""
    return f"{obj!r} from {os.path.abspath(inspect.getfile(obj))}"
