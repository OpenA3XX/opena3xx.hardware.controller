"""Project-specific exception types used across subsystems.

These exception classes provide semantic categories for error handling without
changing business logic. Callers can catch a narrower error type and log or
escalate appropriately.
"""


class OpenA3XXConfigurationException(Exception):
    """Raised when local or remote configuration cannot be parsed or applied."""
    pass


class OpenA3XXNetworkingException(Exception):
    """Raised when network discovery or API reachability checks fail."""
    pass


class OpenA3XXI2CRegistrationException(Exception):
    """Raised when MCP23017 extenders cannot be initialized over the I2C bus."""
    pass


class OpenA3XXRabbitMqPublishingException(Exception):
    """Raised when publishing to RabbitMQ fails (events or keepalive)."""
    pass
