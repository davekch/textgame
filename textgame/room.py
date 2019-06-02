import logging
logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())

from textgame.globals import MOVING, DESCRIPTIONS, INFO, DIRECTIONS, LIGHT


class Room:

    def __init__(self, ID):
        self.id = ID   # unique, similar rooms should have a common keyword in ID
        self.doors = {dir: None for dir in DIRECTIONS}
        # dict that describes the locked/opened state of doors
        self.locked = {dir: {"closed":False, "key":None} for dir in DIRECTIONS}
        # description to print when going in this direction
        self.dir_descriptions = {dir: "" for dir in DIRECTIONS}
        # items that lie around in this room, format {ID: item}
        self.items = {}
        # monsters that are in this room, format {ID: monster}
        self.monsters = {}
        self.visited = False
        self.hiddendoors = {}
        # special_func gets called on Room.check_restrictions
        # which is called when the player enters the room
        self.special_func = None
        self.special_args = {}
        # initialize descriptive information
        self.fill_info()


    def fill_info(self, descript="", sdescript="", value=5,\
                  dark={"now": False, "always": False}, sound=DESCRIPTIONS.NO_SOUND,\
                  hint="", hint_value=2, errors={},\
                  doors={}, hiddendoors={}, locked={}, dir_descriptions={}):
        self.description = descript
        self.shortdescription = sdescript
        self.value = value
        self.dark = dark
        self.sound = sound
        self.hint = hint
        self.hint_value = hint_value
        # errors is a dict that contains error messages that get printed if player
        # tries to move to a direction where there is no door
        for dir in errors:
            if dir not in DIRECTIONS:
                logger.warning("In errors of room {}: {} is not"
                               " a direction".format(self.id, dir))
        self.errors = {dir: MOVING.FAIL_CANT_GO for dir in DIRECTIONS}
        self.errors.update(errors)
        for dir,room in doors.items():
            self.add_connection(dir, room)
        for dir,room in hiddendoors.items():
            self.add_connection(dir, room, hidden=True)
        for dir,lock in locked.items():
            if "closed" not in lock or "key" not in lock:
                logger.warning("locked dict of room {} in direction {} is "
                    "badly formatted".format(self.id, dir))
            if dir not in DIRECTIONS:
                logger.warning("locked dict of room {}: {} is not a direction".format(self.id, dir))
        self.locked.update(locked)
        for dir in dir_descriptions:
            if dir not in DIRECTIONS:
                logger.warning("dir_descriptions dict of room {}: {} is not a direction".format(self.id, dir))
        self.dir_descriptions.update(dir_descriptions)


    def describe(self, long=False):
        long = long or not self.visited
        if self.dark["now"]:
            return DESCRIPTIONS.DARK_L
        descript = self.description if long else self.shortdescription
        for item in self.items.values():
            descript += "\n" + item.describe()
        for monster in self.monsters.values():
            descript += "\n" + monster.describe()
        return descript


    def add_connection(self, dir, room, hidden=False):
        if not dir in DIRECTIONS:
            logger.error("You try to add a connection {} to {} "
                "but this is not a direction".format(dir, self.id))
        if not hidden:
            self.doors[dir] = room
        else:
            self.hiddendoors[dir] = room


    def visit(self):
        if not self.dark["now"]:
            self.visited = True
            return self.value
        return 0


    def get_hint(self):
        """return a tuple of warning and the actual hint
        """
        return (INFO.HINT_WARNING.format(self.hint_value), self.hint)


    def has_light(self):
        """returns true if there's anything inside room that lights it up
        """
        return any([lamp in self.items for lamp in LIGHT])


    def set_specials(self, func, **args):
        self.special_func = func
        self.special_args = args if args else {}


    def check_restrictions(self, player):
        """check if it's dark and call self.special_func
        """
        self.dark["now"] = self.dark["always"] and not (self.has_light() or player.has_light())
        if self.special_func:
            return self.special_func(player, **self.special_args)
        return ""


    def reveal_hiddendoors(self):
        logger.debug("revealing hiddendoors in room {} to {}"\
            .format(self.id, ", ".join([dir for dir in self.hiddendoors])))
        self.doors.update(self.hiddendoors)


    def add_item(self, item):
        if item.id not in self.items:
            self.items[item.id] = item
        else:
            logger.warning("You try to add item {} to room {} but "\
                "it's already there".format(item.id, self.id))


    def add_monster(self, monster):
        if monster.id not in self.monsters:
            self.monsters[monster.id] = monster
        else:
            logger.warning("You try to add monster {} to room {} but "\
                "it's already there".format(monster.id, self.id))
