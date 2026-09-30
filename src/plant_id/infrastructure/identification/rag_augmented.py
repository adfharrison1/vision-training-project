"""Optional RAG inject around identify repos (retrieval: OpenRouter + Qdrant by default)."""

from __future__ import annotations

from plant_id.domain.models import Observation, ObservationResult
from plant_id.domain.repositories import IdentificationRepository
from plant_id.domain.species_retrieval import SpeciesRetrievalRepository
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.identification.vlm_common import format_rag_context


class RagAugmentedIdentificationRepository:
    """Retrieve species context and pass it into the inner identification backend."""

    def __init__(
        self,
        inner: IdentificationRepository,
        retrieval: SpeciesRetrievalRepository,
        settings: Settings,
    ) -> None:
        self._inner = inner
        self._retrieval = retrieval
        self._settings = settings

    @property
    def backend_id(self) -> str:
        return f"rag+{self._inner.backend_id}"

    def identify(
        self,
        observation: Observation,
        *,
        rag_context: str | None = None,
    ) -> tuple[ObservationResult, dict]:
        if rag_context is not None:
            return self._inner.identify(observation, rag_context=rag_context)
        contexts = self._retrieval.retrieve(
            tuple(observation.photo_paths),
            self._settings.retrieval_top_k,
        )
        formatted = format_rag_context(contexts)
        return self._inner.identify(observation, rag_context=formatted or None)
