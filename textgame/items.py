from dataclasses import dataclass
from .messages import m


@dataclass
class Item:
    id: str
    name: str
    description: str
    initlocation: str
    value: int = 0
    takable: bool = True

    def describe(self) -> m:
        return m(self.description)


@dataclass
class Key(Item):
    key_id: int = 0