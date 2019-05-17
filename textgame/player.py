from inspect import signature
from collections import namedtuple
import logging
logger = logging.getLogger("textgame.player")
logger.addHandler(logging.NullHandler())

from textgame.globals import DIRECTIONS, MOVING, INFO, ACTION, LIGHT, DESCRIPTIONS


# return this if a player's method should trigger a yes/no conversation
EnterYesNoLoop = namedtuple("EnterYesNoLoop", ["func"])


def action_method(f):
    """
    wrapper for player methods
    player methods that are mapped to verbs must take a noun as an argument
    """
    n_args = len(signature(f).parameters)
    if n_args == 1:
        # add a dummy argument
        def _f(self, noun):
            return f(self)
        return _f
    elif n_args > 2:
        raise TypeError("Action methods can't have more than 2 arguments")
    return f



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
            return MOVING.DEATH_BY_COWARDICE + self.die()
        else:
            destination = self.location.doors[direction]
            # see if there is a door
            if destination:
                # see if door is open
                if not direction in self.location.locked:
                    # move, but remember previous room
                    self.oldlocation = self.location
                    self.location = destination

                    # spawn monsters before describing the room
                    self.world.spawn_monster(destination)
                    # check if room is dark etc, plus extrawürste
                    msg = destination.check_restrictions(self)
                    msg += destination.describe()
                    if not destination.visited:
                        self.score += destination.visit()
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
            return self.go(direction)


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
                return ACTION.SUCC_TAKE.format(itemid)
            return ACTION.FAIL_TAKE
        return ACTION.NO_SUCH_ITEM.format(itemid)


    def takeall(self):
        if not self.location.items:
            return DESCRIPTIONS.NOTHING_THERE
        if self.location.dark["now"]:
            return DESCRIPTIONS.DARK_S
        response = []
        for itemid in list(self.location.items.keys()):
            response.append(self.take(itemid))
        return '\n'.join(response)


    @action_method
    def list_inventory(self):
        if self.inventory:
            response = "You are now carrying:\n A "
            response += '\n A '.join(self.inventory.keys())
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
            self.drop(item)
        return ACTION.SUCC_DROP


    @action_method
    def die(self):
        pass


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


    @action_method
    def ask_hint(self):
        """
        ask for a hint in the current location,
        if there is one, trigger yes/no conversation if the hint should really
        be displayed
        """
        warning, hint = self.location.get_hint()
        if not hint:
            return INFO.NO_HINT
        # stuff self.hint_conversation inside the EnterYesNoLoop,
        # this will be called during conversation
        return EnterYesNoLoop(self.hint_conversation)

    def hint_conversation(self, really):
        warning, hint = self.location.get_hint()
        if not really:
            return warning
        else:
            # if player really wanted that hint, substract from score and return hint
            self.score -= self.location.hint_value
            return hint
