from inspect import signature
from collections import namedtuple
import random
import logging
logger = logging.getLogger("textgame.player")
logger.addHandler(logging.NullHandler())

from textgame.globals import DIRECTIONS, MOVING, INFO, ACTION, LIGHT, DESCRIPTIONS
from textgame.globals import FIGHTING


# return this if a player's method should trigger a yes/no conversation
EnterYesNoLoop = namedtuple("EnterYesNoLoop", ["func", "denial", "question"])


def player_method(f):
    """
    wrapper for player methods
    player methods that are mapped to verbs must take a noun as an argument
    """
    func = f

    # check signature of f
    n_args = len(signature(f).parameters)
    if n_args == 1:
        # add a dummy argument
        def _f(self, noun):
            return f(self)
        func = _f
    elif n_args > 2:
        raise TypeError("Action methods can't have more than 2 arguments")

    return func


def action_method(f):
    """
    player_method that appends world.update (time passing, daylight handling ...)
    to the passed function
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
    return _f



class Player:
    """
    class to represent the player of the game
    does all the stuff like take drop kill listen ...
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
        self.inventory = {}
        self.status = {"alive": True, "fighting": False, "trapped": False}


    @action_method
    def go(self, direction):
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
                    # move, but remember previous room
                    self.oldlocation = self.location
                    self.location = destination

                    # spawn monsters before describing the room
                    self.world.spawn_monster(destination)
                    # check if room is dark etc, plus extrawürste
                    msg = self.location.check_restrictions(self)
                    msg += self.location.describe()
                    if not self.location.visited:
                        self.score += self.location.visit()
                    return msg
                else:
                    return MOVING.FAIL_DOOR_LOCKED
            else:
                return self.location.errors[direction]


    def goback(self):
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
            return Player.go.undecorated(self, direction)


    @action_method
    def close(self, direction):
        return self.close_or_lock("lock", direction)

    @action_method
    def open(self, direction):
        return self.close_or_lock("open", direction)

    def close_or_lock(self, action, direction):
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
        if not itemid:
            return ACTION.WHICH_ITEM
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
        return ACTION.NO_SUCH_ITEM.format(itemid)


    def takeall(self):
        if not self.location.items:
            return DESCRIPTIONS.NOTHING_THERE
        if self.location.dark["now"]:
            return DESCRIPTIONS.DARK_S
        response = []
        for itemid in list(self.location.items.keys()):
            response.append(Player.take.undecorated(self, itemid))
        return '\n'.join(response)


    @action_method
    def list_inventory(self):
        if self.inventory:
            response = "You are now carrying:\n A "
            response += '\n A '.join(i.name for i in self.inventory.values())
            return response
        return ACTION.NO_INVENTORY


    @action_method
    def drop(self, itemid):
        if itemid == "all":
            return self.dropall()

        if not itemid in self.inventory:
            return ACTION.FAIL_DROP
        # move item from inventory to current room
        self.location.add_item( self.inventory.pop(itemid) )
        return ACTION.SUCC_DROP


    def dropall(self):
        if not self.inventory:
            return ACTION.NO_INVENTORY
        for item in list(self.inventory.keys()):
            Player.drop.undecorated(self, item)
        return ACTION.SUCC_DROP


    @action_method
    def attack(self, monstername):
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
            monster.status["fighting"] = True
            if monster.history == -1:
                return monster.ignoretext
            elif monster.history < 2:
                if random.random() > monster.strength-monster.history/10:
                    monster.kill()
                return FIGHTING.ATTACK
            elif monster.history == 2:
                if random.random() > monster.strength-0.2:
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
        self.oldlocation = self.location


    @action_method
    def look(self):
        return self.location.describe(long=True)


    @action_method
    def listen(self):
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
        if there is one, trigger yes/no conversation if the hint should really
        be displayed
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
        return EnterYesNoLoop(func=hint_conversation, question=warning, denial="ok")
