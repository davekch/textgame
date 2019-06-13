"""
textgame.player
=====================

This module contains a class :class:`textgame.player.Player` that is used to define
what a player is able to do in the game. Every of its methods that get called by
:class:`textgame.parser.Parser` must take a noun (string) as an argument and return
either a string that describes the action or a :class:`textgame.parser.EnterYesNoLoop`.
For convenience, this module provides wrappers for Player methods:

- :func:`textgame.player.player_method`
- :func:`textgame.player.action_method`
"""

from inspect import signature
from collections import OrderedDict
import random
import logging
logger = logging.getLogger("textgame.player")
logger.addHandler(logging.NullHandler())

from textgame.globals import DIRECTIONS, MOVING, INFO, ACTION, LIGHT, DESCRIPTIONS
from textgame.globals import FIGHTING
from textgame.parser import EnterYesNoLoop


def player_method(f):
    """wrapper for player methods

    checks if the method has the right signature, adds a dummy argument if the method doesn't care about nouns. Throws :class:`TypeError` if there are too many arguments.
    """
    func = f

    # check signature of f
    n_args = len(signature(f).parameters)
    if n_args == 1:
        # add a dummy argument
        def _f(self, noun):
            return f(self)
        func = _f
        # preserve (but change) docstring
        func.__doc__ = "decorated by :func:`textgame.player.player_method`\n\n"\
            + (f.__doc__ if f.__doc__ else "")

    elif n_args > 2:
        raise TypeError("Action methods can't have more than 2 arguments")

    return func


def action_method(f):
    """wrapper for player methods

    does the same as :func:`textgame.player.player_method` plus it adds to the return
    value of the original function the output of :func:`textgame.world.World.update`.
    This way it is guaranteed that time passes and fights get managed when the player
    does something.

    Also, this saves the undecorated function in a new attribute ``f.undecorated``.
    """
    func = player_method(f)

    # append self.world.update to the end of every method
    def _f(self, noun):
        msg = func(self, noun)
        if type(msg) is str:
            # the other possibility is EnterYesNoLoop
            msg += self.world.update(self)
        return msg

    # save the undecorated function
    # reason: one might want to call action_methods from other action_methods,
    # in this case nested decorations lead to bugs bc of multiple calls
    # on world.update
    _f.undecorated = f
    # preserve (but change) docstring
    _f.__doc__ = "decorated by :func:`textgame.player.action_method`\n\n"\
        + (f.__doc__ if f.__doc__ else "")

    return _f



class Player:
    """class to represent the player of the game

    - holds an instance of :class:`textgame.world.World` so that its methods can have the widest possible impact on the game
    - ``self.location`` contains the room the player is currently in, ``self.oldlocation`` contains the previous location
    - ``self.inventory`` is a dict mapping the item's IDs to the items the player is carrying
    - ``self.status`` tracks the player's status: ``{"alive": True, "fighting": False, "trapped": False}``
    """

    def __init__(self, world, initlocation):
        self.location = initlocation
        self.oldlocation = None
        # player must know of the whole world so that he can
        # move to other places quickly (eg.)
        self.world = world
        self.score = 0
        self.age = 0    # TODO: maybe this is redundant with world.time
        # dict to contain all the items the player is carrying
        self.inventory = OrderedDict()
        self.status = {"alive": True, "fighting": False, "trapped": False}

        self.random = random.Random()
        logger.debug("seeding player with {}".format(self.world.seed+42))
        self.random.seed(self.world.seed+42)


    @action_method
    def go(self, direction):
        """
        change location to the room in the direction ``noun``. ``noun`` can be
        in :class:`textgame.globals.DIRECTIONS` or 'back'. On different inputs, return
        :class:`textgame.globals.MOVING.FAIL_NOT_DIRECTION`
        """
        if direction == "back":
            return  self.goback()
        elif not direction:
            return MOVING.FAIL_WHERE
        elif direction not in DIRECTIONS:
            return MOVING.FAIL_NOT_DIRECTION

        # this line is in player.cpp but it makes no sense?
        # self.location.check_restrictions(self)
        if self.status["trapped"]:
            return MOVING.FAIL_TRAPPED
        elif self.status["fighting"]:
            # running away from a fight will kill player
            self.status["alive"] = False
            return MOVING.DEATH_BY_COWARDICE
        else:
            destination = self.location.doors[direction]
            # see if there is a door
            if destination:
                # see if door is open
                if not self.location.locked[direction]["closed"]:
                    # how does moving to this direction look like?
                    dir_description = self.location.dir_descriptions[direction]
                    # move, but remember previous room
                    self.oldlocation = self.location
                    self.location = destination

                    # spawn monsters before describing the room
                    self.world.spawn_monster(destination)
                    # check if room is dark etc, plus extrawürste
                    msg = self.location.check_restrictions(self)
                    # if the room is not dark, add dir_description to the beginning
                    if not self.location.dark["now"] and dir_description:
                        msg = dir_description + '\n' + msg
                    msg += self.location.describe()
                    if not self.location.visited:
                        self.score += self.location.visit()
                    return msg
                else:
                    return MOVING.FAIL_DOOR_LOCKED
            else:
                return self.location.errors[direction]


    def goback(self):
        """
        change location to previous location if there's a connection
        """
        if self.oldlocation == self.location:
            return MOVING.FAIL_NO_MEMORY
        # maybe there's no connection to oldlocation
        if not self.oldlocation in self.location.doors.values():
            return MOVING.FAIL_NO_WAY_BACK
        else:
            # find in which direction oldlocation is
            for dir,dest in self.location.doors.items():
                if dest == self.oldlocation:
                    direction = dir
                    break
            return type(self).go.undecorated(self, direction)


    @action_method
    def close(self, direction):
        """
        lock the door in direction ``noun`` if player has a key in inventory
        that fits
        """
        return self._close_or_lock("lock", direction)

    @action_method
    def open(self, direction):
        """
        open the door in direction ``noun`` if player has a key in inventory
        that fits
        """
        return self._close_or_lock("open", direction)

    def _close_or_lock(self, action, direction):
        if direction not in DIRECTIONS:
            return ACTION.FAIL_OPENDIR.format(action)
        # check if there's a door
        if not self.location.doors[direction]:
            return MOVING.FAIL_NO_DOOR
        # check if door is already open/closed
        if action=="open" and not self.location.locked[direction]["closed"]:
            return ACTION.ALREADY_OPEN
        elif action=="lock" and self.location.locked[direction]["closed"]:
            return ACTION.ALREADY_CLOSED
        # check if there are any items that are keys
        if any([i.key for i in self.inventory.values()]):
            # get all keys and try them out
            keys = [i for i in self.inventory.values() if i.key]
            for key in keys:
                if key.key == self.location.locked[direction]["key"]:
                    # open/close the door, depending on action
                    self.location.locked[direction]["closed"] = (action == "lock")
                    return ACTION.NOW_OPEN.format(action)
            return ACTION.FAIL_OPEN
        return ACTION.FAIL_NO_KEY


    @action_method
    def take(self, itemid):
        """
        see if something with the ID ``noun`` is in the items of the current
        location. If yes and if it's takable and not dark, remove it from location
        and add it to inventory
        """
        if not itemid:
            return ACTION.WHICH_ITEM.format("take")
        elif itemid == "all":
            return self.takeall()

        if self.location.dark["now"]:
            return DESCRIPTIONS.DARK_S
        if itemid in self.inventory:
            return ACTION.OWN_ALREADY

        item = self.location.items.get(itemid)
        if item:
            if item.takable:
                # move item from location to inventory
                self.inventory[itemid] = self.location.items.pop(itemid)
                return ACTION.SUCC_TAKE.format(item.name)
            return ACTION.FAIL_TAKE
        elif itemid in self.location.description:
            return ACTION.FAIL_TAKE
        return ACTION.NO_SUCH_ITEM.format(itemid)


    def takeall(self):
        """
        move all items in the current location to inventory
        """
        if not self.location.items:
            return DESCRIPTIONS.NOTHING_THERE
        if self.location.dark["now"]:
            return DESCRIPTIONS.DARK_S
        response = []
        for itemid in list(self.location.items.keys()):
            response.append(type(self).take.undecorated(self, itemid))
        return '\n'.join(response)


    @action_method
    def list_inventory(self):
        """
        return a pretty formatted list of what's inside inventory
        """
        if self.inventory:
            response = "You are now carrying:\n A "
            response += '\n A '.join(i.name for i in self.inventory.values())
            return response
        return ACTION.NO_INVENTORY


    @action_method
    def drop(self, itemid):
        """
        see if something with the ID ``noun`` is in the inventory. If yes, remove
        it from inventory and add it to location
        """
        if not itemid:
            return ACTION.WHICH_ITEM.format("drop")

        if itemid == "all":
            return self.dropall()

        if not itemid in self.inventory:
            return ACTION.FAIL_DROP
        # move item from inventory to current room
        self.location.add_item( self.inventory.pop(itemid) )
        return ACTION.SUCC_DROP


    def dropall(self):
        """
        move all items in the inventory to current location
        """
        if not self.inventory:
            return ACTION.NO_INVENTORY
        for item in list(self.inventory.keys()):
            # type(self) may be Player or a derived class from player
            type(self).drop.undecorated(self, item)
        return ACTION.SUCC_DROP


    @action_method
    def attack(self, monstername):
        """
        kill a monster based on randomness, the monster's strength and on how
        long the fight has been going already. Die if killing fails too often.

        If the history of the monster is -1, the monster's ``ignoretext`` gets returned.
        """
        if not monstername:
            return FIGHTING.WHAT
        monsters = [m for m in self.location.monsters.values() if m.name==monstername]
        # should be max 1
        if len(monsters) == 0:
            # maybe there's a dead one?
            if monstername in [m.name for m in self.location.items.values()]:
                return FIGHTING.ALREADY_DEAD.format(monstername)
            return FIGHTING.NO_MONSTER.format(monstername)

        elif len(monsters) == 1:
            monster = monsters[0]
            if monster.status["singleencounter"]:
                return FIGHTING.ALREADY_GONE.format(monstername)

            monster.status["fighting"] = True
            if monster.history == -1:
                return monster.ignoretext
            elif monster.history < 2:
                if self.random.random() > monster.strength-monster.history/10:
                    monster.kill()
                return FIGHTING.ATTACK
            elif monster.history == 2:
                if self.random.random() > monster.strength-0.2:
                    monster.kill()
                    return FIGHTING.LAST_ATTACK
                self.status["alive"] = False
                return FIGHTING.DEATH

        else:
            logger.error("There's currently more than one monster with "
                "name {} in room {}. This should not be possible!".format(monstername, self.location.id))


    @action_method
    def show_score(self):
        return INFO.SCORE.format(self.score)


    def forget(self):
        """
        set old location to current location
        """
        self.oldlocation = self.location


    @action_method
    def look(self):
        """
        get the long description of the current location.
        Also spawn monsters and check check_restrictions (see :func:`textgame.room.Room.check_restrictions`)
        """
        # spawn monsters before describing the room
        self.world.spawn_monster(self.location)
        # check if room is dark etc, plus extrawürste
        msg = self.location.check_restrictions(self)
        msg += self.location.describe(long=True)
        return msg


    @action_method
    def listen(self):
        """
        get the current room's sound
        """
        return self.location.sound


    def has_light(self):
        """
        returns true if player carries anything that lights a room up
        """
        return any([lamp in self.inventory for lamp in LIGHT])


    @player_method
    def ask_hint(self):
        """
        ask for a hint in the current location,
        if there is one, return :class:`textgame.parser.EnterYesNoLoop` if the hint
        should really be displayed
        """
        warning, hint = self.location.get_hint()
        if not hint:
            return INFO.NO_HINT

        def hint_conversation():
            warning, hint = self.location.get_hint()
            self.score -= self.location.hint_value
            return hint

        # stuff hint_conversation inside the EnterYesNoLoop,
        # this will be called during conversation
        return EnterYesNoLoop(
            question = warning,
            yes = hint_conversation,
            no = "ok."
        )
