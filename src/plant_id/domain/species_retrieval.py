"""Domain port and models for species sheet retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class SpeciesSheet(BaseModel):
    """Species knowledge sheet loaded from YAML (value object)."""

    model_config = ConfigDict(frozen=True)

    catalog_label: str = Field(min_length=1)
    retrieval_text: str = Field(min_length=1)
    context_block: str = Field(min_length=1)


class RetrievedSpeciesContext(BaseModel):
    """One ranked species hit for retrieval or RAG inject."""

    model_config = ConfigDict(frozen=True)

    catalog_label: str = Field(min_length=1)
    score: float
    context_block: str = Field(min_length=1)
    retrieval_text: str | None = None


class SpeciesRetrievalRepository(Protocol):
    """Swappable backend for top-K species sheet retrieval from photos."""

    @property
    def backend_id(self) -> str: ...

    def retrieve(
        self,
        photo_paths: tuple[Path, ...],
        k: int,
    ) -> tuple[RetrievedSpeciesContext, ...]:
        """Return up to k species contexts ranked by score (higher is better)."""
        ...
