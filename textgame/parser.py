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
    """
    :param player: :class:`textgame.player.Player` object
    """

    def __init__(self, player):

        self.player = player

        self.in_yesno = False    # are we inside a yes/no conversation?
        # yesno_backup must be a function that takes a bool and returns
        # user output. it will be executed if yes/no conversation ends with yes
        self.yesno_backup = None

        self.legal_verbs = {
            "": "continue",    # dont do anything on empty input
            "attack": "attack",
            "back": "back",
            "close": "close",
            "d": "down",
            "down": "down",
            "drop": "drop",
            "e": "east",
            "east": "east",
            "enter": "go",
            "go": "go",
            "grab": "take",
            "hear": "listen",
            "hint": "hint",
            "inventory": "inventory",
            "kill": "attack",
            "listen": "listen",
            "lock": "close",
            "look": "look",
            "n": "north",
            "north": "north",
            "open": "open",
            "s": "south",
            "score": "score",
            "south": "south",
            "take": "take",
            "u": "up",
            "up": "up",
            "w": "west",
            "walk": "go",
            "west": "west",
        }

        # this may be used to define synonyms
        self.legal_nouns = {
            "d": "down",
            "e": "east",
            "n": "north",
            "s": "south",
            "u": "up",
            "w": "west",
        }

        # the lambdas are there because the values in this dict must be
        # callable with exactly one argument
        self.actionmap = {
            "attack": player.attack,
            "back": lambda x: player.go("back"),
            "continue": lambda x: "",
            "down": lambda x: player.go("down"),
            "drop": player.drop,
            "east": lambda x: player.go("east"),
            "go": player.go,
            "hint": player.ask_hint,
            "inventory": player.list_inventory,
            "listen": player.listen,
            "look": player.look,
            "close": player.close,
            "north": lambda x: player.go("north"),
            "open": player.open,
            "score": player.show_score,
            "south": lambda x: player.go("south"),
            "take": player.take,
            "up": lambda x: player.go("up"),
            "west": lambda x: player.go("west"),
        }

        self.check()


    def lookup_verb(self, verb):
        return self.legal_verbs.get(verb)


    def lookup_noun(self, noun):
        return self.legal_nouns.get(noun)


    def check(self):
        """
        check if every verb in self.legal_verbs has a function mapped to.
        if not, the game will crash on the input of this verb

        logs the error
        """
        for verb in set(self.legal_verbs.values()):
            if verb not in self.actionmap:
                logger.error("{} is a legal verb but has no definition"
                    "in actionmap".format(verb))


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
        return self.actionmap[verb](noun)


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
