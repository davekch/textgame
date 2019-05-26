import logging
logger = logging.getLogger("textgame.parser")
logger.addHandler(logging.NullHandler())

from textgame.globals import INFO
from textgame.player import EnterYesNoLoop


class Parser:
    """
    makes sense of user's input, performs actions,
    defines which words are allowed to use and maps them to player's methods
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
            "look": "look",
            "n": "north",
            "north": "north",
            "s": "south",
            "score": "score",
            "south": "south",
            "take": "take",
            "u": "up",
            "up": "up",
            "w": "west",
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
            "north": lambda x: player.go("north"),
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
        check if every verb in self.legal_verbs has a function mapped to
        if not, the game will crash on the input of this verb
        """
        for verb in set(self.legal_verbs.values()):
            if verb not in self.actionmap:
                logger.error("{} is a legal verb but has no definition"
                    "in actionmap".format(verb))


    def do(self, verb, noun):
        """
        call function associated with verb with noun as argument
        check if parser should fall into yesno loop
        """
        result = self.actionmap[verb](noun)
        if type(result) is EnterYesNoLoop:
            self.in_yesno = True
            # result.func takes bool as only argument, save it
            self.yesno_backup = result
            # what does result.func say at the beginning?
            return result.func(False)
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
        the return value is what will be printed to the user
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
                # execute and return the method that asked for a yes before
                result = self.yesno_backup.func(True)
                # maybe we have a nested yes no loop
                if type(result) is EnterYesNoLoop:
                    self.in_yesno = True
                    # result.func takes bool as only argument, save it
                    self.yesno_backup = result
                    # what does result.func say at the beginning?
                    return result.func(False)
                return result
            else:
                self.in_yesno = False
                return self.yesno_backup.denial

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

        return result
