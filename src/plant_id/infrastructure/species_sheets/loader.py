"""Load and validate species sheet YAML from disk."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from plant_id.domain.species_retrieval import SpeciesSheet

PROTOTYPES_YAML = "prototypes.yaml"

FORBIDDEN_RETRIEVAL_PATTERNS = (
    re.compile(r"\bin frame\b", re.IGNORECASE),
    re.compile(r"\bphoto(graph)?\b", re.IGNORECASE),
    re.compile(r"\boxford\b", re.IGNORECASE),
    re.compile(r"\bimage_\d+\b", re.IGNORECASE),
)


def species_sheets_dir(root: Path | None = None) -> Path:
    from plant_id.infrastructure.config.settings import _project_root

    base = root or _project_root()
    return base / "resources" / "species_sheets"


def load_species_sheet(path: Path) -> SpeciesSheet:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Sheet YAML must be a mapping: {path}")
    return SpeciesSheet.model_validate(payload)


def list_sheet_paths(sheets_dir: Path | None = None) -> list[Path]:
    directory = sheets_dir or species_sheets_dir()
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.glob("*.yaml")
        if path.is_file() and path.name != PROTOTYPES_YAML
    )


def load_all_sheets(sheets_dir: Path | None = None) -> dict[str, SpeciesSheet]:
    sheets: dict[str, SpeciesSheet] = {}
    for path in list_sheet_paths(sheets_dir):
        sheet = load_species_sheet(path)
        if sheet.catalog_label in sheets:
            raise ValueError(
                f"Duplicate catalog_label {sheet.catalog_label!r} in {path} "
                f"and existing sheet."
            )
        sheets[sheet.catalog_label] = sheet
    return sheets


def validate_retrieval_text(text: str) -> list[str]:
    issues: list[str] = []
    for pattern in FORBIDDEN_RETRIEVAL_PATTERNS:
        if pattern.search(text):
            issues.append(f"retrieval_text matches forbidden pattern {pattern.pattern!r}")
    return issues


def validate_sheet_catalog_membership(
    sheet: SpeciesSheet,
    *,
    catalog_labels: set[str],
) -> list[str]:
    issues: list[str] = []
    if sheet.catalog_label not in catalog_labels:
        issues.append(
            f"catalog_label {sheet.catalog_label!r} is not in the species catalog"
        )
    issues.extend(validate_retrieval_text(sheet.retrieval_text))
    return issues
