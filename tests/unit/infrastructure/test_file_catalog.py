from pathlib import Path

import pytest

from plant_id.domain.exceptions import IdentificationError
from plant_id.infrastructure.config.settings import Settings
from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog


def test_file_catalog_loads_default_catalog() -> None:
    settings = Settings()
    catalog = FileSpeciesCatalog(settings.species_catalog_path)

    names = catalog.list_class_names()

    assert len(names) == 102
    assert names[0] == "pink primrose"
    assert names[-1] == "blackberry lily"


def test_file_catalog_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    with pytest.raises(IdentificationError, match="not found"):
        FileSpeciesCatalog(missing)


def test_file_catalog_rejects_empty_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.write_text("\n\n", encoding="utf-8")
    with pytest.raises(IdentificationError, match="empty"):
        FileSpeciesCatalog(empty)
