from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(
        env_prefix="PLANT_ID_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_host: str = Field(
        default="http://127.0.0.1:11434",
        description="Base URL for the local Ollama server.",
    )
    ollama_timeout_seconds: float = Field(
        default=600.0,
        gt=0,
        description=(
            "Maximum seconds to wait for a single Ollama chat request "
            "(vision calls on 2b typically finish within a few minutes)."
        ),
    )
    ollama_think: bool = Field(
        default=False,
        description=(
            "When true, allow qwen3 thinking mode on Ollama chat requests. "
            "Default false avoids token-budget death spirals on closed-set identify."
        ),
    )
    ollama_content_retry_enabled: bool = Field(
        default=True,
        description=(
            "When true, retry once when the model returns empty content but JSON in "
            "thinking, or a wholly empty/truncated response."
        ),
    )
    ollama_content_retry_max: int = Field(
        default=1,
        ge=1,
        le=1,
        description="Maximum content-channel retries per observation (fixed at 1).",
    )
    invalid_label_retry_enabled: bool = Field(
        default=True,
        description=(
            "When true, retry once when the model JSON uses a species_label outside "
            "the closed catalog."
        ),
    )
    vision_model: str = Field(
        default="qwen3-vl:2b",
        description=(
            "Ollama vision model tag (default 2b for fast local iteration; "
            "override e.g. qwen3-vl:8b for comparison)."
        ),
    )
    min_ollama_version: str = Field(
        default="0.33.3",
        description="Minimum supported Ollama server version.",
    )
    species_catalog_path: Path = Field(
        default_factory=lambda: _project_root()
        / "resources"
        / "species_catalog"
        / "default.txt",
        description="Newline-delimited closed-set species label list for identification.",
    )
    uncertainty_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Top prediction confidence below this marks result as uncertain.",
    )
    identify_artifacts_dir: Path = Field(
        default_factory=lambda: _project_root() / "identify_artifacts",
        description="Directory for CLI identify/demo per-observation JSON artifacts.",
    )
    eval_runs_dir: Path = Field(
        default_factory=lambda: _project_root() / "eval_runs",
        description="Root directory for eval run bundles (manifest, report, grouped artifacts).",
    )
    prompt_version: str = Field(
        default="closed-set-v4.3",
        description="Prompt template version recorded in artifacts.",
    )
    opik_enabled: bool = Field(
        default=False,
        description="Export Ollama VLM traces to a local self-hosted Opik server.",
    )
    opik_base_url: str = Field(
        default="http://127.0.0.1:5173/api",
        description="Self-hosted Opik API base URL (local only — no Comet cloud).",
    )
    opik_project_name: str = Field(
        default="plant-id",
        description="Opik project name for identification traces.",
    )
    vlm_cloud_api_key: str | None = Field(
        default=None,
        description=(
            "API key for OpenAI-compatible cloud VLM inference (backend vlm-cloud). "
            "Read only from PLANT_ID_VLM_CLOUD_API_KEY."
        ),
    )
    vlm_cloud_base_url: str = Field(
        default="https://api.fireworks.ai/inference/v1",
        description="OpenAI-compatible base URL for cloud VLM chat completions.",
    )
    vlm_cloud_model: str = Field(
        default="accounts/fireworks/models/qwen3-vl-8b-instruct",
        description="Model identifier on the configured cloud VLM endpoint.",
    )
    vlm_cloud_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        description="Maximum seconds to wait for a single cloud VLM chat completion.",
    )
    vlm_cloud_vendor: str | None = Field(
        default=None,
        description="Optional label for traces and eval reports (e.g. fireworks).",
    )
    vlm_cloud_reasoning_effort: str | None = Field(
        default="none",
        description=(
            "OpenAI-compatible reasoning_effort for chat completions (Fireworks DeepSeek V4 "
            "defaults to high thinking when omitted). Use 'none' to disable reasoning tokens; "
            "low/medium/high/max enable thinking. Set empty env var to omit and "
            "use provider default."
        ),
    )
    vlm_openrouter_api_key: str | None = Field(
        default=None,
        description="OpenRouter API key for Nemotron multimodal retrieval embeddings.",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter OpenAI-compatible API base URL.",
    )
    openrouter_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        description="HTTP timeout for OpenRouter embedding requests.",
    )
    openrouter_http_referer: str = Field(
        default="https://github.com/uk-plant-id",
        description="HTTP-Referer header required by OpenRouter for some routes.",
    )
    openrouter_app_title: str = Field(
        default="plant-id-retrieval",
        description="X-Title header sent to OpenRouter.",
    )
    retrieval_embed_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        description="OpenRouter embedding model id for multimodal prototypes.",
    )
    species_sheets_dir: Path = Field(
        default_factory=lambda: _project_root() / "resources" / "species_sheets",
        description="Directory of species sheet YAML files.",
    )
    retrieval_index_dir: Path = Field(
        default_factory=lambda: _project_root() / "artifacts" / "retrieval_index",
        description="Built OpenRouter index manifest and vectors (gitignored).",
    )
    qdrant_url: str = Field(
        default="http://127.0.0.1:6333",
        description="Qdrant HTTP API URL for retrieval seed/query.",
    )
    qdrant_collection: str = Field(
        default="species_sheets_v1",
        description="Qdrant collection name for species prototypes.",
    )
    qdrant_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="HTTP timeout for Qdrant client calls.",
    )
    retrieval_max_prototypes_per_species: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max Oxford train images indexed per species sheet.",
    )
    retrieval_search_multiplier: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Fetch limit multiplier before aggregating per species.",
    )
    retrieval_backend: str = Field(
        default="nemotron-prototype",
        description="Retrieval: nemotron-prototype (OpenRouter+Qdrant) or describe-hybrid.",
    )
    retrieval_top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Default top-K species sheets for retrieval and RAG inject.",
    )
    rag_enabled: bool = Field(
        default=False,
        description="When true, inject retrieved context blocks into VLM identify prompt.",
    )
    retrieval_bm25_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for BM25 in describe-hybrid fusion.",
    )
    retrieval_embed_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Text-embed weight for describe-hybrid fusion (fallback backend).",
    )
    retrieval_text_embed_backend: str = Field(
        default="hashing",
        description="Text embedder for describe-hybrid fallback: hashing or sentence-transformers.",
    )
    retrieval_text_embed_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="sentence-transformers model when backend is sentence-transformers.",
    )
    sheet_synth_prompt_version: str = Field(
        default="sheet-synth-v1",
        description="Prompt version recorded in synthesised sheet provenance.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
