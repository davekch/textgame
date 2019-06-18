# textgame
A python library for text based adventure games.

## Usage
This library provides classes for
 - rooms that can be connected to each other
 - items/weapons that can be placed to certain rooms
 - monsters that can sit around in rooms or be randomly spawned in certain rooms
 - a player that can
   - move through the rooms, look around, listen
   - take items and do stuff with them
   - fight the monsters
 - a parser that translates user input into player actions

By writing a new player class that inherits from `textgame.Player`, arbitrary activities can be made possible for the player. See [the example](example.py) or some [more examples](https://davekch.github.io/textgame/source/examples.html) for more.

Creating a map for the game is just as easy as writing a dict/json-file that contains descriptions for all the rooms and then loading them in your program:

```python
from textgame.world import World
import json

with open("myrooms.json") as f:
    rooms = json.load(f)

world = World(rooms=rooms)
```

See in [the example](example.py) how `myrooms.json` should be formatted. Creating items, weapons or monsters follows the same scheme.

The parser is restricted to understand commands consisting of two or one words. The first word in the command must be mapped to a function or a method of Player that will then be called with the second word as an argument. This is done by writing a class that inherits from `textgame.parser.Parser`  (again, see [the example](example.py)) or some [more examples](https://davekch.github.io/textgame/source/examples.html).

The output to the user is always returned as a string. This way you can build your adventure game as a terminal application or integrate it to a website or write a chat bot like so:

```python
# terminal application
while not command == "quit":
    command = input("> ")
    response = parser.understand(command)
    print(response)

# chatbot (pseudocode)
while chatbot.is_active:
    command = chatbot.get_message()
    response = parser.understand(command)
    chatbot.send_message(response)
```

#### Example output from [example.py](example.py)
```
You are standing in the middle of a wide open field. In the west the silhouette
of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest
reaches to the east.
A wolf runs towards you!

> go south
You are in a wide rocky pit. An aisle leads upwards to the north.
A sparkling diamond lies around!

> take diamond
You carry now a diamond.

> listen
It's all quiet.

> go west
The slope is too steep here.

> inventory
You are now carrying:
 A diamond

> scream
AAAAAAAAAHHH!!!

>
```

## Installation
```
git clone https://github.com/davekch/textgame.git
cd textgame
pip3 install -e .
```
