from ..messages import m

DIRECTIONS = [m("north"), m("east"), m("south"), m("west"), m("up"), m("down")]
YES = m("yes")
NO = m("no")

default_verb_synonyms = {
    "go": ["enter", "walk"],
    "take": ["grab", "get"],
    "listen": ["hear"],
    "fight": ["kill", "attack"],
    "close": ["lock"],
    "north": ["n"],
    "east": ["e"],
    "south": ["s"],
    "west": ["w"],
    "up": ["u"],
    "down": ["d"],
}
default_noun_synonyms = {
    "north": ["n"],
    "east": ["e"],
    "south": ["s"],
    "west": ["w"],
    "up": ["u"],
    "down": ["d"],
    "yes": ["y"],
}


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
    NOTHING_THERE = m("There's nothing here.")


class ACTION(DefaultMessage):
    OWN_ALREADY = m("You already have it!")
    WHICH_ITEM = m("Please specify an item you want to {}.")
    SUCC_DROP = m("Dropped.")
    SUCC_TAKE = m("You carry now a {}.")
    FAIL_DROP = m("You don't have one.")
    FAIL_TAKE = m("You can't take that.")
    NO_SUCH_ITEM = m("I see no {} here.")
    NO_SUCH_FIGHT = m("There is no {} that wants to fight with you.")
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
