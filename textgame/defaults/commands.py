from __future__ import annotations
from typing import Callable, List, Optional
from ..registry import command_registry, Registry
from ..state import State, PlayerStatus
from ..messages import MessageType, MultipleChoiceQuestion, m, YesNoQuestion
from ..defaults.words import DIRECTIONS, INFO, MOVING, ACTION, DESCRIPTIONS
from ..things import Key, Monster, Takable, Weapon


defaultcommand_registry: Registry[
    Callable[[str, State], Optional[MessageType]]
] = Registry()


def use_defaults(exclude: List[str] = None):
    """register the commands that are defined in textgame.defaults.commands and are not already registered"""
    exclude = exclude or []
    for command, func in defaultcommand_registry.items():
        if command not in exclude and command not in command_registry:
            command_registry.register(command, func)


@defaultcommand_registry.register("go")
def go(direction: str, state: State) -> Optional[MessageType]:
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

                # call the hook of the new location
                msg = state.player_location.call_hook(state)
                # if the room is not dark, add dir_description to the beginning
                if (
                    not state.player_location.is_dark() or state.lighting()
                ) and dir_description:
                    # put the directional description first
                    msg = m(dir_description) + msg
                msg += state.player_location.describe(light=state.lighting())
                # if the room is not dark and we weren't here before, add the room's score
                if not state.player_location.visited and (
                    state.lighting() or not state.player_location.is_dark()
                ):
                    state.score += state.player_location.visit()
                return msg
            else:
                return MOVING.FAIL_DOOR_LOCKED
        else:
            return state.player_location.describe_error(direction)


def goback(state: State) -> Optional[MessageType]:
    """
    change location to previous location if there's a connection
    """
    if (
        not state.player_location_old
        or state.player_location_old == state.player_location
    ):
        return MOVING.FAIL_NO_MEMORY
    # maybe there's no connection to location_old
    if not state.player_location.connects_to(state.player_location_old.id):
        return MOVING.FAIL_NO_WAY_BACK
    else:
        # find in which direction location_old is
        for dir, dest in state.player_location.get_open_connections().items():
            if dest == state.player_location_old:
                direction = str(dir)
                break
        return go(direction, state)


@defaultcommand_registry.register("north")
def go_north(_, state: State) -> Optional[MessageType]:
    return go("north", state)


@defaultcommand_registry.register("east")
def go_east(_, state: State) -> Optional[MessageType]:
    return go("east", state)


@defaultcommand_registry.register("south")
def go_south(_, state: State) -> Optional[MessageType]:
    return go("south", state)


@defaultcommand_registry.register("west")
def go_west(_, state: State) -> Optional[MessageType]:
    return go("west", state)


@defaultcommand_registry.register("up")
def go_up(_, state: State) -> Optional[MessageType]:
    return go("up", state)


@defaultcommand_registry.register("down")
def go_down(_, state: State) -> Optional[MessageType]:
    return go("down", state)


@defaultcommand_registry.register("close")
def close(direction: str, state: State) -> Optional[MessageType]:
    """
    lock the door in direction ``direction`` if player has a key in inventory
    that fits
    """
    return _close_or_lock("lock", direction, state)


@defaultcommand_registry.register("open")
def open(direction: str, state: State) -> Optional[MessageType]:
    """
    open the door in direction ``direction`` if player has a key in inventory
    that fits
    """
    return _close_or_lock("open", direction, state)


def _close_or_lock(action, direction: str, state: State) -> Optional[MessageType]:
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


@defaultcommand_registry.register("look")
def look(_, state: State) -> Optional[MessageType]:
    """
    get the long description of the current location.
    """
    msg = state.player_location.call_hook(state)
    msg += state.player_location.describe(long=True, light=state.lighting())
    return msg


@defaultcommand_registry.register("take")
def take(itemid: str, state: State) -> Optional[MessageType]:
    """
    see if something with the ID ``itemid`` is in the items of the current
    location. If yes and if it's takable and not dark, remove it from location
    and add it to inventory
    """
    if not itemid:
        return ACTION.WHICH_ITEM.format("take")
    elif itemid == "all":
        return takeall(state)

    if state.player_location.is_dark() and not state.lighting():
        return DESCRIPTIONS.DARK_S
    if itemid in state.inventory:
        return ACTION.OWN_ALREADY

    takables = state.player_location.things.items(filter=[Takable])
    item = takables.get(itemid)
    if item:
        if item.takable:
            # move item from location to inventory
            state.inventory.add(item)
            return ACTION.SUCC_TAKE.format(item.name)
        return ACTION.FAIL_TAKE
    elif (
        itemid in state.player_location
        or itemid in state.player_location.description
        or any(
            itemid in thing.describe()
            for thing in state.player_location.things.values()
        )
    ):
        return ACTION.FAIL_TAKE
    return ACTION.NO_SUCH_ITEM.format(itemid)


def takeall(state: State) -> Optional[MessageType]:
    """
    move all items in the current location to inventory
    """
    if not state.player_location.things.keys():
        return DESCRIPTIONS.NOTHING_THERE
    if state.player_location.is_dark():
        return DESCRIPTIONS.DARK_S
    response = m()
    for itemid in state.player_location.things.keys():
        response += take(itemid, state)
    return response


@defaultcommand_registry.register("inventory")
def list_inventory(_: str, state: State) -> Optional[MessageType]:
    """
    return a pretty formatted list of what's inside inventory
    """
    if state.inventory:
        response = m("You are now carrying:")
        for i in state.inventory.values():
            response += m(" A " + i.name)
        return response
    return ACTION.NO_INVENTORY


@defaultcommand_registry.register("drop")
def drop(itemid: str, state: State) -> Optional[MessageType]:
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
    state.player_location.things.add(state.inventory.pop(itemid))
    return ACTION.SUCC_DROP


def dropall(state: State) -> Optional[MessageType]:
    """
    move all items in the inventory to current location
    """
    if not state.inventory:
        return ACTION.NO_INVENTORY
    for item in state.inventory.keys():
        drop(item, state)
    return ACTION.SUCC_DROP


@defaultcommand_registry.register("score")
def show_score(_: str, state: State) -> Optional[MessageType]:
    return INFO.SCORE.format(state.score)


@defaultcommand_registry.register("listen")
def listen(_: str, state: State) -> Optional[MessageType]:
    return m(state.player_location.sound)


@defaultcommand_registry.register("hint")
def ask_hint(_: str, state: State) -> Optional[MessageType]:
    """
    ask for a hint in the current location,
    if there is one, return :class:`textgame.parser.EnterYesNoLoop` if the hint
    should really be displayed
    """
    warning, hint = state.player_location.get_hint()
    if not hint:
        return INFO.NO_HINT

    def hint_conversation() -> m:
        state.score -= state.player_location.hint_value
        return hint

    # stuff hint_conversation inside the EnterYesNoLoop,
    # this will be called during conversation
    return YesNoQuestion(question=warning, yes=hint_conversation, no=m("ok."))


@defaultcommand_registry.register("fight")
def fight(noun: str, state: State) -> Optional[MessageType]:
    if noun and noun not in state.player_location.things:
        return ACTION.NO_SUCH_FIGHT.format(noun)
    weapons = state.inventory.values(filter=[Weapon])
    if not weapons:
        return ACTION.NO_WEAPONS
    if len(weapons) > 1:
        return MultipleChoiceQuestion(
            question=m("Which weapon do you want to use?"),
            answers={w.id: lambda: use_weapon(w.id, state) for w in weapons},
        )
    return use_weapon(list(weapons)[0].id, state)


def use_weapon(weapon_id: str, state: State) -> m:
    # assumes that the weapon is in inventory;
    # this is guaranteed by fight, which calls this function
    weapon: Weapon = state.inventory.get(weapon_id)  # type: ignore
    msg = m()
    for monster in state.player_location.things.values(filter=[Monster]):
        monster.health -= weapon.calculate_damage(state.random)
        msg += m(f"You use the {weapon.name} against the {monster.name}!")
    if not msg:
        return ACTION.NO_SUCH_FIGHT.format("monster")
    return msg
