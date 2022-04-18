def yield_sequence(seq):
    """
    returns a function that returns each element of seq on subsequent calls.
    can be used to mock random
    """
    it = iter(seq)
    return lambda *args: next(it)
