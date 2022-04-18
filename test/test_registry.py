from textgame import registry


class TestSkipHooks:

    def test_skip_precommandhookdecorator(self):
        skips = ["time", "fight"]

        @registry.skip_precommandhook(skips)
        def test1(arg):
            return arg
        
        assert registry.get_precommandhook_skips(test1) == skips
        assert test1("arg") == "arg"

        # register a dummy hook
        registry.register_precommandhook("something", lambda *args, **kwargs: None)

        # skip all
        @registry.skip_precommandhook
        def test2(arg):
            return arg
        
        assert registry.get_precommandhook_skips(test2) == ["something"]
        assert test2("arg") == "arg"

    def test_skip_postcommandhookdecorator(self):
        skips = ["time", "fight"]

        @registry.skip_postcommandhook(skips)
        def test1(arg):
            return arg
        
        assert registry.get_postcommandhook_skips(test1) == skips
        assert test1("arg") == "arg"

        # register a dummy hook
        registry.register_postcommandhook("something", lambda *args, **kwargs: None)

        # skip all
        @registry.skip_postcommandhook
        def test2(arg):
            return arg
        
        assert "something" in registry.get_postcommandhook_skips(test2)
        assert test2("arg") == "arg"
    
    def teardown_method(self, test_method):
        # unregister everything
        for hook in registry.precommandhook_registry:
            registry.unregister_precommandhook(hook)
        for hook in registry.postcommandhook_registry:
            registry.unregister_postcommandhook(hook)