Improving the parser
======================

In the last tutorial we added the command "wave" that could be used with "wand". Maybe the user can't figure out they have to type in "wave wand" and try out "swing wand" or "shake wand". The idea is correct, only the wording is different. If we want the user to succeed on these inputs, we can define sets of synonyms for commands and nouns.

.. code-block:: python

    # main.py

    # ...
    parser = Parser()
    # define some synonyms
    parser.update_verb_synonyms({
        "wave": ["swing", "shake"],
    })

:func:`textgame.parser.Parser.update_verb_synonyms` takes a dictionary where the keys are registered commands and the values are lists of verbs that should be mapped to the command.

A similar method exists for nouns:

.. code-block:: python

    parser.update_noun_synonyms({
        "diamond": ["gem", "crystal"],
    })
