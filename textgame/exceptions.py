class ConfigurationError(ValueError):
    pass


class UniqueConstraintError(ValueError):
    pass


class StoreLimitExceededError(RuntimeError):
    pass