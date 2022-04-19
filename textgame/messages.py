from __future__ import annotations
from functools import wraps
from typing import Protocol, Union, Callable, Dict, List


class MessageType(Protocol):
    def to_message(self) -> m:
        ...


def wrap_m(func: Callable[..., str | MessageType]) -> Callable[..., MessageType]:
    """decorator that converts the returned value of func into m if it's a string"""

    @wraps(func)
    def returns_m(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return m(result)
        return result

    return returns_m


class YesNoQuestion:
    """
    :param question: a yes/no question
    :type question: m
    :param yes: m to return or a function with signature ``f() -> m`` or ``f() -> EnterYesNoLoop`` that should get called if player answeres 'yes' to the question
    :param no: same as yes
    """

    def __init__(
        self,
        question: m | str,
        yes: str | MessageType | Callable[[], MessageType],
        no: str | MessageType | Callable[[], MessageType],
    ):
        self.question = question
        self._yes = yes
        self._no = no

    @wrap_m
    def yes(self) -> MessageType:
        """
        if yes is callable, return its result, else return it
        """
        if callable(self._yes):
            return self._yes()
        return self._yes  # type: ignore

    @wrap_m
    def no(self) -> MessageType:
        """
        if no is callable, return its result, else return it
        """
        if callable(self._no):
            return self._no()
        return self._no  # type: ignore

    def to_message(self) -> m:
        return m(self.question)


class MultipleChoiceQuestion:
    def __init__(
        self,
        question: m | str,
        answers: Dict[m | str, MessageType | Callable[[], MessageType]],
        cancel: bool = True,
    ):
        self._question = question
        answers_list = list(answers.items())
        if cancel:
            answers_list.append((m("Cancel"), m("Ok.")))
        self.answers = {str(i + 1): a for i, a in enumerate(answers_list)}

    def to_message(self) -> m:
        q = m(self._question)
        for i, answer in self.answers.items():
            q += m(f" ({i}) {answer[0]}")
        return q

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} question={self._question!r} answers={self.answers}>"

    @wrap_m
    def get_response(self, choice: str) -> MessageType:
        _, response = self.answers[choice]
        if callable(response):
            return response()
        return response

    @property
    def possible_answers(self) -> List[str]:
        return list(self.answers.keys())


class m:

    seperator = "\n"
    translations: Dict[str, str] = {}

    def __init__(self, msg: str | m = "", needs_answer: bool = False):
        # don't accidentally nest messages
        if isinstance(msg, m):
            msg = msg.data
        elif msg and not isinstance(msg, str):
            raise TypeError(
                f"Can't convert {msg!r} to type {self.__class__.__name__!r}"
            )

        self._data = msg

    def to_message(self) -> m:
        return self

    @property
    def data(self):
        if self._data in self.translations:
            return self.translations[self._data]
        return self._data

    def format(self, *args, **kwargs) -> m:
        return m(self.data.format(*args, **kwargs))

    def replace(self, old: str, new: str) -> m:
        return m(self.data.replace(old, new))

    @classmethod
    def update_translations(cls, dict):
        cls.translations.update(dict)

    def __add__(self, other) -> m:
        if isinstance(other, m):
            other = other.data

        # only add a seperator if there is already data
        if self.data and other:
            result = self.data + self.seperator + other
        elif not self.data:
            result = other
        elif not other:
            result = self.data
        return m(result)

    def __iadd__(self, other) -> m:
        # return a new instance instead of mutating this one, otherwise
        # the messages add up over time
        return self + other

    def __hash__(self):
        return hash(self.data)

    def __bool__(self) -> bool:
        return bool(self.data)

    def __contains__(self, string: str) -> bool:
        return string in self.data

    def __str__(self) -> str:
        return self.data or ""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {repr(self.data or '')}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, m):
            return self.data == other.data
        elif isinstance(other, str):
            return self.data == other
        else:
            raise NotImplementedError
