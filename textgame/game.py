# TODO: docstring

import logging
logger = logging.getLogger("textgame.game")
logger.addHandler(logging.NullHandler())


class Game:
    def __init__(self, player, parser):
        self.player = player
        self.parser = parser
        self.world = player.world
        self.gameover = False

    def play(self, command):
        func, noun = self.parser.understand(command)
        try:
            result = func(noun)
        except TypeError:
            logger.debug("the function {} takes no arguments, discard noun".format(func.__name__))
            result = func()
        response = self.parser.make_sense_of(result)
        response += "\n" + self.world.update(self.player)
        self.gameover = not self.player.status["alive"]
        return response
