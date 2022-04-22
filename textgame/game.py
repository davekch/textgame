"""
textgame.game
=====================

This module provides the :class:`textgame.game.Game` class, which will handle the flow of the game once
everything is set up.

.. code-block:: python

    from textgame.game import Game

    # ...
    game = Game(myplayer, myparser)
    while not game.over():
        command = input("> ")
        reply = game.play(command)
        print(reply)
"""


import pickle
import os
import logging
logger = logging.getLogger("textgame.game")
logger.addHandler(logging.NullHandler())


class Game:
    """
    :param player: :class:`textgame.player.Player` object
    :param parser: :class:`textgame.parser.Parser` object
    """

    def __init__(self, player, parser):
        self.player = player
        self.parser = parser
        self.world = player.world
        self.gameover = False

    def play(self, command):
        """
        passes the command to :func:`textgame.parser.Parser.understand` and executes the resulting function. The result gets checked by
        :func:`textgame.parser.Parser.make_sense_of`. If the called function is not marked as timeless (see :func:`textgame.player.timeless`),
        :func:`textgame.world.World.update` gets called as well and the result added.

        :param command: command given by user
        :type command: string
        :returns: string
        """
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

    def over(self):
        """returns ``True`` if the player is dead
        """
        return self.gameover

    def save_game(self, path="", session=""):
        """
        pickle the player and parser object

        :param path: directory where to store the game
        :param session: some identifyer. If empty or None, the pickle gets saved as ``textgame.pickle``, else ``textgame_<session>.pickle``.
        :type session: string
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
        load previously saved pickle

        :param path: parent directory of the pickle
        :param session: some identifyer. If empty or None, ``textgame.pickle`` gets loaded, else ``textgame_<session>.pickle``.
        :type session: string
        """
        if session:
            filename = os.path.join(path, "textgame_{}.pickle".format(session))
        else:
            filename = os.path.join(path, "textgame.pickle")
        with open(filename, "rb") as f:
            logger.info("reinitializing game with loaded player and parser object")
            player, parser = pickle.load(f)
            return cls(player, parser)
