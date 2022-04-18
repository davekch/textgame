class ConfigurationError(ValueError):
    pass


class UniqueConstraintError(ValueError):
    pass


class StoreLimitExceededError(RuntimeError):
    pass


class FactoryNotFoundError(KeyError):
    pass


class ModeNotFoundError(KeyError):
    pass


class ThingNotFoundError(KeyError):
    pass
