"""CSV helpers for spectrum and analysis rows."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable


def write_csv_rows(
    rows: Iterable[Any],
    output_path: str | Path,
    *,
    fieldnames: list[str] | None = None,
) -> Path:
    """Write dictionaries or dataclass instances to a CSV file."""

    normalized_rows = [_row_to_dict(row) for row in rows]
    if not normalized_rows:
        raise ValueError("rows must not be empty")

    if fieldnames is None:
        fieldnames = _fieldnames_from_rows(normalized_rows)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(normalized_rows)
    return output_path


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    if is_dataclass(row) and not isinstance(row, type):
        return asdict(row)
    raise TypeError("rows must contain dictionaries or dataclass instances")


def _fieldnames_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames
