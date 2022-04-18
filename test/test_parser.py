from textgame.parser import CommandParser, Command, YesNoAnswer, YesNoParser, Dictionary


class TestSimpleParser:
    def test_parse_yesno(self):
        parser = YesNoParser()
        assert parser.parse_input("quack") == YesNoAnswer.INVALID
        assert parser.parse_input("yes") == YesNoAnswer.YES
        assert parser.parse_input("no") == YesNoAnswer.NO
        Dictionary.update_synonyms({"no": ["quack"]})
        assert parser.parse_input("quack") == YesNoAnswer.NO

    def test_parse_command(self):
        parser = CommandParser()
        assert parser.parse_input("take lamp") == Command("take", "lamp")
        Dictionary.update_synonyms({"take": ["grab"]})
        assert parser.parse_input("grab lamp") == Command("take", "lamp")
        Dictionary.update_synonyms({"lamp": ["light"]})
        assert parser.parse_input("grab light") == Command("take", "lamp")
