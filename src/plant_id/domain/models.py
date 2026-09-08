"""Domain models for plant identification."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from plant_id.domain.exceptions import InvalidObservationError


class Observation(BaseModel):
    """One plant sighting with 1–3 photographs of the same individual."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(min_length=1)
    photo_paths: tuple[Path, ...]

    @field_validator("photo_paths", mode="before")
    @classmethod
    def coerce_photo_paths(cls, value: object) -> tuple[Path, ...]:
        if isinstance(value, Path):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(Path(path) for path in value)
        raise InvalidObservationError("photo_paths must be a path or a list of paths.")

    @model_validator(mode="after")
    def validate_photo_count(self) -> Observation:
        count = len(self.photo_paths)
        if count < 1 or count > 3:
            raise InvalidObservationError(
                f"An observation must include 1 to 3 photograph paths; got {count}."
            )
        return self


class Prediction(BaseModel):
    """A single ranked species hypothesis."""

    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1, le=3)
    species_label: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ObservationResult(BaseModel):
    """Structured identification output shared by all runtime backends."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(min_length=1)
    predictions: tuple[Prediction, ...] = Field(min_length=1, max_length=3)
    model_tag: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    uncertain: bool = False

    @model_validator(mode="after")
    def validate_prediction_order(self) -> ObservationResult:
        ranks = [prediction.rank for prediction in self.predictions]
        expected = list(range(1, len(self.predictions) + 1))
        if ranks != expected:
            raise ValueError(
                "Predictions must be ranked consecutively from 1 "
                f"(expected {expected}, got {ranks})."
            )
        return self
