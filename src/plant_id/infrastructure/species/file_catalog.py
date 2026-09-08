"""Load a closed-set species vocabulary from a text file."""

from __future__ import annotations

from pathlib import Path

from plant_id.domain.exceptions import IdentificationError


class FileSpeciesCatalog:
    """Load species class names from a newline-delimited text file."""

    def __init__(self, catalog_path: Path) -> None:
        self._catalog_path = catalog_path
        self._class_names = self._load(catalog_path)

    @property
    def catalog_path(self) -> Path:
        return self._catalog_path

    def list_class_names(self) -> list[str]:
        return list(self._class_names)

    @staticmethod
    def _load(path: Path) -> tuple[str, ...]:
        if not path.is_file():
            raise IdentificationError(f"Species catalog file not found: {path}")
        names = tuple(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if not names:
            raise IdentificationError(f"Species catalog is empty: {path}")
        return names
