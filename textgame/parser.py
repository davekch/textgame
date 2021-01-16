"""
textgame.parser
=====================

This module's main class is :class:`textgame.parser.Parser`. The parser can take
user input, call a function that's associated to the input and return to the user a
message describing what happened.

Use ``actionmap`` and ``legal_verbs`` to define how verbs should be mapped to functions, eg:

.. code-block:: python

   parser.actionmap.update({
    "scream": player.scream
   })
   parser.legal_verbs.update({
    "scream": "scream",
    "shout": "scream"
   })

You can use ``legal_nouns`` to define synonyms for nouns.

A parser is the only thing needed to during the main loop of a game:

.. code-block:: python

   parser = textgame.parser.Parser(player)
   while player.status["alive"]:
       response = parser.understand( input("> ") )
       print(response)


This module also provides :class:`textgame.parser.EnterYesNoLoop`. If a function
called by the parser returns an ``EnterYesNoLoop`` instead of a string, the parser falls
into a mode where it only allows 'yes' and 'no' as an answer. An object of type
``EnterYesNoLoop`` also provides strings/functions to print/call for each case.

Example: a player method that saves the user from drinking poison

.. code-block:: python

   @action_method
   def drink(self, noun):
       if noun == "poison":

           def actually_do_it():
               self.status["alive"] = False
               return "You drink the poison and die."

           return textgame.parser.EnterYesNoLoop(
                question = "Do you really want to drink poison?",
                yes = actually_do_it,
                no = "You stay alive")
       else:
           # ...

"""

from collections import namedtuple
import pickle
import os
import logging
logger = logging.getLogger("textgame.parser")
logger.addHandler(logging.NullHandler())

from textgame.globals import INFO


class EnterYesNoLoop:
    """
    :param question: a yes/no question
    :type question: string
    :param yes: string to return or a function with signature ``f() -> str`` or ``f() -> EnterYesNoLoop`` that should get called if player answeres 'yes' to the question
    :param no: same as yes
    """

    def __init__(self, question, yes, no):
        self.question = question
        self._yes = yes
        self._no = no

    def yes(self):
        """
        if yes is callable, return its result, else return it
        """
        if callable(self._yes):
            return self._yes()
        return self._yes

    def no(self):
        """
        if no is callable, return its result, else return it
        """
        if callable(self._no):
            return self._no()
        return self._no


class Parser:

    def __init__(self):

        self.in_yesno = False    # are we inside a yes/no conversation?
        # yesno_backup must be a function that takes a bool and returns
        # user output. it will be executed if yes/no conversation ends with yes
        self.yesno_backup = None

        self.legal_verbs = {}
        self.update_verb_synonyms({
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
        })

        # this may be used to define synonyms
        self.legal_nouns = {}
        self.update_noun_synonyms({
            "north": ["n"],
            "east": ["e"],
            "south": ["s"],
            "west": ["w"],
            "up": ["u"],
            "down": ["d"],
        })
        self.actionmap = {}


    def set_actionmap(self, actionmap):
        """
        :param actionmap: dictionary as returned by func:`textgame.player.Player.get_registered_methods`
        """
        self.actionmap = actionmap
        self.legal_verbs.update({c: c for c in actionmap.keys()})


    def update_verb_synonyms(self, synonym_dict):
        # TODO: docstring
        for command, synonyms in synonym_dict.items():
            if type(synonyms) is not list:
                raise TypeError("synonyms must be defined as a list")
            for s in synonyms:
                self.legal_verbs[s] = command

    def update_noun_synonyms(self, synonym_dict):
        # TODO: docstring
        for noun, synonyms in synonym_dict.items():
            if type(synonyms) is not list:
                raise TypeError("synonyms must be defined as a list")
            for s in synonyms:
                self.legal_nouns[s] = noun


    # def save_game(self, path="", session=""):
    #     """
    #     dump self.player as textgame_session.pickle
    #     """
    #     if session:
    #         filename = os.path.join(path, "textgame_{}.pickle".format(session))
    #     else:
    #         filename = os.path.join(path, "textgame.pickle")
    #     logger.info("saving game to {}".format(filename))
    #     with open(filename, "wb") as f:
    #         pickle.dump(self.player, f, pickle.HIGHEST_PROTOCOL)
    #     return INFO.SAVED
    #
    #
    # def load_game(self, path="", session=""):
    #     """
    #     load textgame_session.pickle (player object) and reinitialize parser with it
    #     """
    #     if session:
    #         filename = os.path.join(path, "textgame_{}.pickle".format(session))
    #     else:
    #         filename = os.path.join(path, "textgame.pickle")
    #     try:
    #         with open(filename, "rb") as f:
    #             logger.info("reinitializing parser with loaded player object")
    #             self.__init__(pickle.load(f))
    #     except FileNotFoundError:
    #         return "There's no game with the name '{}'.".format(session)
    #     return INFO.LOADED


    def lookup_verb(self, verb):
        return self.legal_verbs.get(verb)


    def lookup_noun(self, noun):
        return self.legal_nouns.get(noun)


    def check_synonyms(self):
        """
        checks if every known verb appears in the actionmap. Raises `KeyError` if otherwise
        """
        not_mapped = set(self.legal_verbs.values()).difference(set(self.actionmap.keys()))
        if not_mapped != set():
            raise KeyError("These verbs are not mapped to a function: {}".format(", ".join(not_mapped)))


    def check_result(self, result):
        """
        checks if result is EnterYesNoLoop or str, if it's EnterYesNoLoop,
        return the question and fall back to yes/no mode
        """
        if type(result) is str:
            return result
        else:
            # assume that result is of type enteryesnoloop
            self.in_yesno = True
            self.yesno_backup = result
            return result.question


    def do(self, verb, noun):
        """
        call function associated with verb with noun as argument
        """
        try:
            result = self.actionmap[verb](noun)
        except TypeError:
            logger.debug("the function {} takes no arguments, discard noun".format(verb))
            result = self.actionmap[verb]()
        return result


    def _split_input(self, input):
        """
        take input and return verb and noun
        """
        args = input.split()
        if len(args) > 2:
            # this gets catched in Parser.understand
            raise ValueError()
        elif len(args) == 2:
            verb, noun = args
        elif len(args) == 1:
            verb = args[0]
            noun = ""
        else:
            verb = ""
            noun = ""
        return verb, noun


    def understand(self, input):
        """
        based on the input, perform player method and return its output
        the return value is what can be printed to the user
        """
        try:
            verb, noun = self._split_input(input)
        except ValueError:
            return INFO.TOO_MANY_ARGUMENTS

        # if a yes/no conversation is going on, only allow yes/no as answers
        if self.in_yesno:
            if verb != "yes" and verb != "no":
                return INFO.YES_NO
            elif verb == "yes":
                self.in_yesno = False
                # return the yes case
                result = self.yesno_backup.yes()
                return self.check_result(result)
            else:
                self.in_yesno = False
                # return the no case
                result = self.yesno_backup.no()
                return self.check_result(result)

        commandverb = self.lookup_verb(verb)
        commandnoun = self.lookup_noun(noun)
        # if noun is illegal, reset to it's original value and feed it to
        # the actionmethods. More creative output if erronous input :)
        if not commandnoun:
            commandnoun = noun
        logger.debug("I understood: verb={} noun={}".format(repr(commandverb), repr(commandnoun)))

        # illegal nouns are okay but illegal verbs are not
        if not commandverb:
            return INFO.NOT_UNDERSTOOD

        # perform the associated method
        result = self.do(commandverb, commandnoun)

        return self.check_result(result)
