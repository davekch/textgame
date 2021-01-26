# TODO: docstring

import pickle
import os
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
        if not getattr(func, "timeless", False):
            response += self.world.update(self.player)
        response += "\n"
        self.gameover = not self.player.status["alive"]
        return response


    def save_game(self, path="", session=""):
        """
        dump self.player as textgame_session.pickle
        """
        if session:
            filename = os.path.join(path, "textgame_{}.pickle".format(session))
        else:
            filename = os.path.join(path, "textgame.pickle")
        logger.info("saving game to {}".format(filename))
        with open(filename, "wb") as f:
            pickle.dump((self.player, self.parser), f, pickle.HIGHEST_PROTOCOL)


    @classmethod
    def load_game(cls, path="", session=""):
        """
        load textgame_session.pickle (player object) and reinitialize parser with it
        """
        if session:
            filename = os.path.join(path, "textgame_{}.pickle".format(session))
        else:
            filename = os.path.join(path, "textgame.pickle")
        with open(filename, "rb") as f:
            logger.info("reinitializing game with loaded player and parser object")
            player, parser = pickle.load(f)
            return cls(player, parser)
