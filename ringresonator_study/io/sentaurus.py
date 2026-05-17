"""CSV adapters for Sentaurus Device-derived electrical tables."""

from __future__ import annotations

import csv
from pathlib import Path


def read_sentaurus_capacitance_rows(path: str | Path) -> list[dict[str, float]]:
    """Read voltage/capacitance rows with common Sentaurus-style aliases."""

    with Path(path).open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row")
        return [_normalize_row(row) for row in reader]


def _normalize_row(row: dict[str, str | None]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key, value in row.items():
        if key is None or value in {None, ""}:
            continue
        canonical = _canonical_name(key)
        number = float(value)
        if canonical == "capacitance_ff":
            normalized["capacitance_f"] = number * 1e-15
        elif canonical == "capacitance_pf":
            normalized["capacitance_f"] = number * 1e-12
        else:
            normalized[canonical] = number
    if "voltage" not in normalized or "capacitance_f" not in normalized:
        raise ValueError("Sentaurus rows require voltage and capacitance")
    return normalized


def _canonical_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    aliases = {
        "v": "voltage",
        "voltage_v": "voltage",
        "bias": "voltage",
        "bias_voltage": "voltage",
        "capacitance": "capacitance_f",
        "capacitance_f": "capacitance_f",
        "capacitance_ff": "capacitance_ff",
        "capacitance_pf": "capacitance_pf",
        "junction_current": "junction_current_a",
        "junction_current_a": "junction_current_a",
        "current_a": "junction_current_a",
    }
    return aliases.get(normalized, normalized)
