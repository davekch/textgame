from textgame.messages import m


class TestM:
    def test_str(self):
        test = m("test")
        assert str(test) == "test"
        assert repr(test) == '<m "test">'

    def test_nesting(self):
        test = m("test")
        assert m(test) == m("test")

    def test_concat(self):
        test = m("line 1")
        test += m("line 2")
        assert str(test) == "line 1\nline 2"
        test += m()
        assert str(test) == "line 1\nline 2", "a newline was wrongly added"
        test += m("line 3")
        assert str(test) == "line 1\nline 2\nline 3", "newlines are messed up somehow"
        m.seperator = " "
        test2 = m("word1")
        test2 += m("word2")
        assert str(test2) == "word1 word2"
        m.seperator = "\n"  # reset

    def test_translations(self):
        m.translations.update({"no": "nein"})
        test = m("no")
        assert str(test) == "nein"
        assert m("test") == "test"  # rest remains the same
        # reverse the change
        m.translations = {}
