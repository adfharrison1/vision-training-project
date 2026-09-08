"""Domain-layer exceptions."""


class DomainError(Exception):
    """Base class for domain errors."""


class InvalidObservationError(DomainError):
    """Raised when an observation violates domain rules."""


class IdentificationError(DomainError):
    """Raised when identification fails after the observation is valid."""

    def __init__(self, message: str, *, raw: dict | None = None) -> None:
        super().__init__(message)
        self.raw = raw or {}
