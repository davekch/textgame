from ..registry import register_command
from ..state import State, PlayerStatus
from ..messages import m, MOVING, ACTION, DESCRIPTIONS
from ..room import DIRECTIONS
from ..things import Key


@register_command("go")
def go(direction: str, state: State) -> m:
    """
    change location to the room in the direction ``noun``. ``noun`` can be
    in :class:`textgame.globals.DIRECTIONS` or 'back'. On different inputs, return
    :class:`textgame.globals.MOVING.FAIL_NOT_DIRECTION`
    """
    if direction == "back":
        return goback(state)
    elif not direction:
        return MOVING.FAIL_WHERE
    elif direction not in DIRECTIONS:
        return MOVING.FAIL_NOT_DIRECTION

    if state.player_status == PlayerStatus.TRAPPED:
        return MOVING.FAIL_TRAPPED
    elif state.player_status == PlayerStatus.FIGHTING:
        # running away from a fight will kill player
        state.player_status = PlayerStatus.DEAD
        return MOVING.DEATH_BY_COWARDICE
    else:
        destination = state.player_location.get_connection(direction)
        # see if there is a door
        if destination:
            # see if door is open
            if not state.player_location.is_locked(direction):
                # how does moving to this direction look like?
                dir_description = state.player_location.describe_way_to(direction)
                # move, but remember previous room
                state.player_location_old = state.player_location
                state.player_location = destination

                # if the room is not dark, add dir_description to the beginning
                if not state.player_location.is_dark() and dir_description:
                    msg = dir_description
                else:
                    msg = m()
                msg += state.player_location.describe()
                if not state.player_location.visited:
                    state.score += state.player_location.visit()
                return msg
            else:
                return MOVING.FAIL_DOOR_LOCKED
        else:
            return state.player_location.describe_error(direction)


def goback(state: State) -> m:
    """
    change location to previous location if there's a connection
    """
    if state.player_location_old == state.player_location:
        return MOVING.FAIL_NO_MEMORY
    # maybe there's no connection to location_old
    if not state.player_location.connects_to(state.player_location_old):
        return MOVING.FAIL_NO_WAY_BACK
    else:
        # find in which direction location_old is
        for dir,dest in state.player_location.doors.items():
            if dest == state.player_location_old:
                direction = dir
                break
        return go(direction, state)


@register_command("north")
def go_north(_, state: State) -> m:
    return go("north", state)

@register_command("east")
def go_east(_, state: State) -> m:
    return go("east", state)

@register_command("south")
def go_south(_, state: State) -> m:
    return go("south", state)

@register_command("west")
def go_west(_, state: State) -> m:
    return go("west", state)

@register_command("up")
def go_up(_, state: State) -> m:
    return go("up", state)

@register_command("down")
def go_down(_, state: State) -> m:
    return go("down", state)


@register_command("close")
def close(direction: str, state: State) -> m:
    """
    lock the door in direction ``direction`` if player has a key in inventory
    that fits
    """
    return _close_or_lock("lock", direction, state)


@register_command("open")
def open(direction: str, state: State) -> m:
    """
    open the door in direction ``direction`` if player has a key in inventory
    that fits
    """
    return _close_or_lock("open", direction, state)


def _close_or_lock(action, direction: str, state: State) -> m:
    if direction not in DIRECTIONS:
        return ACTION.FAIL_OPENDIR.format(action)
    # check if there's a door
    if not state.player_location.has_connection_in(direction):
        return MOVING.FAIL_NO_DOOR
    # check if door is already open/closed
    if action == "open" and not state.player_location.is_locked(direction):
        return ACTION.ALREADY_OPEN
    elif action == "lock" and state.player_location.is_locked(direction):
        return ACTION.ALREADY_CLOSED
    # check if there are any items that are keys
    keys = [i for i in state.inventory.values() if isinstance(i, Key)]
    if keys:
        # try them all out
        for key in keys:
            if key.key_id == state.player_location.get_door_code(direction):
                # open/close the door, depending on action
                state.player_location.set_locked(direction, action == "lock")
                return ACTION.NOW_OPEN.format(action)
        return ACTION.FAIL_OPEN
    return ACTION.FAIL_NO_KEY


@register_command("look")
def look(_, state: State) -> m:
    """
    get the long description of the current location.
    """
    return state.player_location.describe(long=True)


@register_command("take")
def take(itemid: str, state: State) -> m:
    """
    see if something with the ID ``itemid`` is in the items of the current
    location. If yes and if it's takable and not dark, remove it from location
    and add it to inventory
    """
    if not itemid:
        return ACTION.WHICH_ITEM.format("take")
    elif itemid == "all":
        return takeall(state)

    if state.player_location.dark["now"]:
        return DESCRIPTIONS.DARK_S
    if itemid in state.inventory:
        return ACTION.OWN_ALREADY

    item = state.player_location.get_item(itemid)
    if item:
        if item.takable:
            # move item from location to inventory
            state.inventory[itemid] = state.player_location.pop_item(itemid)
            return ACTION.SUCC_TAKE.format(item.name)
        return ACTION.FAIL_TAKE
    elif itemid in state.player_location.description:
        return ACTION.FAIL_TAKE
    return ACTION.NO_SUCH_ITEM.format(itemid)


def takeall(state: State) -> m:
    """
    move all items in the current location to inventory
    """
    if not state.player_location.items:
        return DESCRIPTIONS.NOTHING_THERE
    if state.player_location.is_dark():
        return DESCRIPTIONS.DARK_S
    response = m()
    for itemid in state.player_location.get_itemnames():
        response += take(itemid, state)
    return response


@register_command("inventory")
def list_inventory(_: str, state: State):
    """
    return a pretty formatted list of what's inside inventory
    """
    if state.inventory:
        response = m("You are now carrying:")
        for i in state.inventory.values():
            response += m("A " + i.name)
        return response
    return ACTION.NO_INVENTORY


@register_command("drop")
def drop(itemid: str, state: State):
    """
    see if something with the ID ``noun`` is in the inventory. If yes, remove
    it from inventory and add it to location
    """
    if not itemid:
        return ACTION.WHICH_ITEM.format("drop")

    if itemid == "all":
        return dropall(state)

    if not itemid in state.inventory:
        return ACTION.FAIL_DROP
    # move item from inventory to current room
    state.player_location.add_item(state.inventory.pop(itemid))
    return ACTION.SUCC_DROP


def dropall(state: State):
    """
    move all items in the inventory to current location
    """
    if not state.inventory:
        return ACTION.NO_INVENTORY
    for item in list(state.inventory.keys()):
        drop(item, state)
    return ACTION.SUCC_DROP