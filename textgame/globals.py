"""
textgame.globals
=====================

This is a collection of predefined messages that get returned to the user. If you don't like them, modify them like this:

.. code-block:: python

   from textgame.globals import MOVING
   MOVING.FAIL_CANT_GO = "It's not possible to go there"

"""

from collections import namedtuple


DIRECTIONS = ["north", "west", "south", "east", "up", "down"]
# items that lighten rooms up
LIGHT = ["lamp", "torch", "candles"]


MOVING = namedtuple("MOVING", [])
MOVING.DEATH_BY_COWARDICE = "Coward! Running away from a fight is generally not a good idea. Your back doesn't defend itself.\n"
MOVING.FAIL_ALREADY_LOCKED = "The door is already locked!"
MOVING.FAIL_CANT_GO = "You can't go in this direction."
MOVING.FAIL_DOOR_LOCKED = "The door is locked."
MOVING.FAIL_NO_DOOR = "There is no door in this direction."
MOVING.FAIL_NO_MEMORY = "I can't remember where you came from."
MOVING.FAIL_NO_WAY_BACK = "There is no direct way to go back."
MOVING.FAIL_NOT_DIRECTION = "That's not a direction."
MOVING.FAIL_TRAPPED = "You're trapped! You can't leave this room for now."
MOVING.FAIL_WHERE = "Tell me where to go!"
MOVING.SUCC_DOOR_LOCKED = "The door is now locked!"


DESCRIPTIONS = namedtuple("DESCRIPTIONS", [])
DESCRIPTIONS.DARK_L = "It's pitch dark here. You can't see anything. Anytime soon, you'll probably get attacked by some night creature."
DESCRIPTIONS.DARK_S = "I can't see anything!"
DESCRIPTIONS.NO_SOUND = "It's all quiet."


ACTION = namedtuple("ACTION", [])
ACTION.OWN_ALREADY = "You already have it!"
ACTION.WHICH_ITEM = "Please specify an item you want to {}."
ACTION.SUCC_DROP = "Dropped."
ACTION.SUCC_TAKE = "You carry now a {}."
ACTION.FAIL_DROP = "You don't have one."
ACTION.FAIL_TAKE = "You can't take that."
ACTION.NO_SUCH_ITEM = "I see no {} here."
DESCRIPTIONS.NOTHING_THERE = "There's nothing here."
ACTION.NO_INVENTORY = "You don't have anything with you."
ACTION.FAIL_OPENDIR = "I can only {0} doors if you tell me the direction. Eg. '{0} west'."
ACTION.FAIL_NO_KEY = "You have no keys!"
ACTION.ALREADY_OPEN = "The door is already open."
ACTION.ALREADY_CLOSED = "The door is already closed."
ACTION.FAIL_OPEN = "None of your keys fit."
ACTION.NOW_OPEN = "You take the key and {} the door."

INFO = namedtuple("INFO", [])
INFO.HINT_WARNING = "I have a hint for you, but it will cost you {} points. Do you want to hear it?"
INFO.NIGHT_COMES_IN = "The sun has set. Night comes in."
INFO.NO_HINT = "I don't have any special hints for you."
INFO.NOT_UNDERSTOOD = "I don't understand that."
INFO.NOTHING = "Nothing happens."
INFO.SCORE = "Your score is {}."
INFO.TOO_MANY_ARGUMENTS = "Please restrict your command to two words."
INFO.YES_NO = "Please answer yes or no."


FIGHTING = namedtuple("FIGHTING", [])
FIGHTING.DARK_DEATH = "A {} certainly has better night vision than you do. At least this was a fast and painless death for you."
FIGHTING.ALREADY_DEAD = "The {} is already dead!"
FIGHTING.NO_MONSTER = "There is no {} to attack."
FIGHTING.ATTACK = "You attack the beast."
FIGHTING.LAST_ATTACK = "For dear life you start one last attack against the fiend."
FIGHTING.DEATH = "Your enemy has gone fully berserk. Badly injured and somewhat aghast of your own inferiority in this fight, you crawl backwards, a last hopeless attempt in saving your life. Goodbye, blue sky."
FIGHTING.SURVIVED_ATTACK = "The {} has survived your attack and is very angry at you!"
FIGHTING.IGNORE = "Ignoring such a dangerous beast is a really bad idea."
FIGHTING.DEFEND_REMINDER = "You must defend yourself! A {} is a serious threat to your life."
FIGHTING.SUCCESS = "You killed the {}."
FIGHTING.LOSER = "You should consider working on your fighting technique. Your amateurish attempts didn't stop the {} from killing you."
FIGHTING.WHAT = "Attack what?"
FIGHTING.ALREADY_GONE = "The {} is already gone."
