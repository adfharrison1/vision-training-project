"""Unit tests for species sheet validation."""

from __future__ import annotations

from pathlib import Path

from plant_id.infrastructure.species_sheets.loader import (
    load_species_sheet,
    validate_retrieval_text,
    validate_sheet_catalog_membership,
)


def test_pilot_sheets_validate_against_catalog() -> None:
    root = Path(__file__).resolve().parents[3]
    sheets_dir = root / "resources" / "species_sheets"
    catalog_path = root / "resources" / "species_catalog" / "default.txt"
    labels = {
        line.strip()
        for line in catalog_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    for path in sheets_dir.glob("*.yaml"):
        if path.name == "prototypes.yaml":
            continue
        sheet = load_species_sheet(path)
        issues = validate_sheet_catalog_membership(sheet, catalog_labels=labels)
        assert issues == [], issues


def test_forbidden_retrieval_patterns() -> None:
    issues = validate_retrieval_text("Typical campanula bells in frame.")
    assert issues
