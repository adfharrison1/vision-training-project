"""Validate committed species sheet YAML (CI-friendly, no API keys)."""

from __future__ import annotations

import sys

from plant_id.infrastructure.species.file_catalog import FileSpeciesCatalog
from plant_id.infrastructure.species_sheets.loader import (
    list_sheet_paths,
    load_species_sheet,
    validate_sheet_catalog_membership,
)


def main() -> int:
    from plant_id.infrastructure.config.settings import _project_root

    sheets_dir = _project_root() / "resources" / "species_sheets"
    paths = list_sheet_paths(sheets_dir)
    if not paths:
        print(f"No sheet YAML files under {sheets_dir}", file=sys.stderr)
        return 1

    catalog = FileSpeciesCatalog(_project_root() / "resources" / "species_catalog" / "default.txt")
    catalog_labels = set(catalog.list_class_names())
    failed = False
    for path in paths:
        sheet = load_species_sheet(path)
        issues = validate_sheet_catalog_membership(sheet, catalog_labels=catalog_labels)
        if issues:
            failed = True
            print(f"{path}:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
    if failed:
        return 1
    print(f"Validated {len(paths)} species sheet(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
