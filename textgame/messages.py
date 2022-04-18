from __future__ import annotations
from functools import wraps
from typing import Protocol, Union, Callable, Dict, List


class MessageType(Protocol):
    def to_message(self) -> m:
        ...


def wrap_m(func: Callable[..., str | m]) -> Callable[..., m]:
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

    def __init__(self, question: m, yes: Union[m, Callable], no: Union[m, Callable]):
        self.question = question
        self._yes = yes
        self._no = no

    @wrap_m
    def yes(self) -> m:
        """
        if yes is callable, return its result, else return it
        """
        if callable(self._yes):
            return self._yes()
        return self._yes

    @wrap_m
    def no(self) -> m:
        """
        if no is callable, return its result, else return it
        """
        if callable(self._no):
            return self._no()
        return self._no

    def to_message(self) -> m:
        return m(self.question)


class MultipleChoiceQuestion:
    def __init__(
        self, question: m, answers: Dict[m, m | Callable[[], m]], cancel: bool = True
    ):
        self._question = question
        answers = list(answers.items())
        if cancel:
            answers.append((m("Cancel"), m("Ok.")))
        self.answers = {str(i + 1): a for i, a in enumerate(answers)}

    def to_message(self) -> m:
        q = self._question
        for i, answer in self.answers.items():
            q += m(f" ({i}) {answer[0]}")
        return q

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} question={self._question!r} answers={self.answers}>"

    @wrap_m
    def get_response(self, choice: str) -> m:
        _, response = self.answers[choice]
        if callable(response):
            return response()
        return response

    @property
    def possible_answers(self) -> List[str]:
        return self.answers.keys()


class m:

    seperator = "\n"
    translations = {}

    def __init__(self, msg: str = "", needs_answer: bool = False):
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

    def __eq__(self, other: Union[str, m]) -> bool:
        if isinstance(other, m):
            return self.data == other.data
        elif isinstance(other, str):
            return self.data == other
        else:
            raise NotImplementedError


class DefaultMessage:
    pass


class INFO(DefaultMessage):
    HINT_WARNING = m(
        "I have a hint for you, but it will cost you {} points. Do you want to hear it?"
    )
    SUNSET = m("The sun has set. Night comes in.")
    SUNRISE = m("The sun is rising! A new day begins")
    NO_HINT = m("I don't have any special hints for you.")
    NOT_UNDERSTOOD = m("I don't understand that.")
    NO_VALID_ANSWER = m(
        "That's not a valid answer to the question. Possible answers are: {}"
    )
    NOTHING = m("Nothing happens.")
    SCORE = m("Your score is {}.")
    TOO_MANY_ARGUMENTS = m("Please restrict your command to two words.")
    YES_NO = m("Please answer yes or no.")
    SAVED = m("Game saved!")
    LOADED = m("Game loaded!")


class MOVING(DefaultMessage):
    DEATH_BY_COWARDICE = m(
        "Coward! Running away from a fight is generally not a good idea. Your back doesn't defend itself."
    )
    FAIL_ALREADY_LOCKED = m("The door is already locked!")
    FAIL_CANT_GO = m("You can't go in this direction.")
    FAIL_DOOR_LOCKED = m("The door is locked.")
    FAIL_NO_DOOR = m("There is no door in this direction.")
    FAIL_NO_MEMORY = m("I can't remember where you came from.")
    FAIL_NO_WAY_BACK = m("There is no direct way to go back.")
    FAIL_NOT_DIRECTION = m("That's not a direction.")
    FAIL_TRAPPED = m("You're trapped! You can't leave this room for now.")
    FAIL_WHERE = m("Tell me where to go!")
    SUCC_DOOR_LOCKED = m("The door is now locked!")


class DESCRIPTIONS(DefaultMessage):
    DARK_L = m(
        "It's pitch dark here. You can't see anything. Anytime soon, you'll probably get attacked by some night creature."
    )
    DARK_S = m("I can't see anything!")
    NO_SOUND = m("It's all quiet.")
    NOTHING_THERE = "There's nothing here."


class ACTION(DefaultMessage):
    OWN_ALREADY = m("You already have it!")
    WHICH_ITEM = m("Please specify an item you want to {}.")
    SUCC_DROP = m("Dropped.")
    SUCC_TAKE = m("You carry now a {}.")
    FAIL_DROP = m("You don't have one.")
    FAIL_TAKE = m("You can't take that.")
    NO_SUCH_ITEM = m("I see no {} here.")
    NO_SUCH_FIGHT = m("There is no {} which wants to fight with you.")
    NO_INVENTORY = m("You don't have anything with you.")
    NO_WEAPONS = m("You don't have any weapons!")
    FAIL_OPENDIR = m(
        "I can only {0} doors if you tell me the direction. Eg. '{0} west'."
    )
    FAIL_NO_KEY = m("You have no keys!")
    ALREADY_OPEN = m("The door is already open.")
    ALREADY_CLOSED = m("The door is already closed.")
    FAIL_OPEN = m("None of your keys fit.")
    NOW_OPEN = m("You take the key and {} the door.")
