from ..messages import m

DIRECTIONS = [m("north"), m("east"), m("south"), m("west"), m("up"), m("down")]
YES = m("yes")
NO = m("no")

default_verb_synonyms = {
    "go": ["enter", "walk"],
    "take": ["grab"],
    "listen": ["hear"],
    "attack": ["kill"],
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