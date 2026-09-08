from plant_id.domain.exceptions import (
    DomainError,
    IdentificationError,
    InvalidObservationError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(InvalidObservationError, DomainError)
    assert issubclass(IdentificationError, DomainError)
