from textgame.parser import SimpleParser, Command, YesNoAnswer, ParsedInput


class TestSimpleParser:
    def test_parse_yesno(self):
        parser = SimpleParser()
        assert parser.parse_yesno("quack") == YesNoAnswer.INVALID
        assert parser.parse_yesno("yes") == YesNoAnswer.YES
        assert parser.parse_yesno("no") == YesNoAnswer.NO
        parser.update_noun_synonyms({"no": ["quack"]})
        assert parser.parse_yesno("quack") == YesNoAnswer.NO

    def test_parse_command(self):
        parser = SimpleParser()
        assert parser.parse_command("take lamp") == Command("take", "lamp")
        parser.update_verb_synonyms({"take": ["grab"]})
        assert parser.parse_command("grab lamp") == Command("take", "lamp")
        parser.update_noun_synonyms({"lamp": ["light"]})
        assert parser.parse_command("grab light") == Command("take", "lamp")

    def test_parse_input(self):
        parser = SimpleParser()
        assert parser.parse_input("eat fish") == ParsedInput(
            Command, Command("eat", "fish")
        )
        assert parser.parse_input("yes") == ParsedInput(YesNoAnswer, YesNoAnswer.YES)
        assert parser.parse_input("throw bottle at goblin") == ParsedInput(None)
