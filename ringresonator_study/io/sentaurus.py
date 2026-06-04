"""CSV adapters for Sentaurus Device-derived electrical tables."""

from __future__ import annotations

import csv
from pathlib import Path

from ringresonator_study.modulation.voltage_models import (
    TableVoltageOpticalModel,
    provisional_voltage_model,
)


def load_sentaurus_voltage_model(
    path: str | Path | None = None,
    *,
    allow_extrapolation: bool = False,
) -> TableVoltageOpticalModel:
    """Load a Sentaurus-derived voltage/ne/ng/loss CSV as a voltage model.

    When no Sentaurus optical export is available yet, call without ``path`` to
    get a small provisional model with placeholder optical data.
    """

    if path is None:
        return provisional_voltage_model(allow_extrapolation=allow_extrapolation)

    return TableVoltageOpticalModel(
        read_sentaurus_voltage_rows(path),
        allow_extrapolation=allow_extrapolation,
    )


def read_sentaurus_voltage_rows(path: str | Path) -> list[dict[str, float]]:
    """Read voltage/ne/ng/loss rows with common Sentaurus-style aliases."""

    with Path(path).open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row")
        return [_normalize_voltage_row(row) for row in reader]


def read_sentaurus_capacitance_rows(path: str | Path) -> list[dict[str, float]]:
    """Read voltage/capacitance rows with common Sentaurus-style aliases."""

    with Path(path).open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row")
        return [_normalize_capacitance_row(row) for row in reader]


def _normalize_voltage_row(row: dict[str, str | None]) -> dict[str, float]:
    normalized = _normalize_row_values(row)
    required = {"voltage", "n_eff", "loss_db_per_cm"}
    missing = sorted(required - normalized.keys())
    if missing:
        raise ValueError(f"Sentaurus voltage rows require: {', '.join(missing)}")
    return normalized


def _normalize_capacitance_row(row: dict[str, str | None]) -> dict[str, float]:
    normalized = _normalize_row_values(row)
    if "voltage" not in normalized or "capacitance_f" not in normalized:
        raise ValueError("Sentaurus rows require voltage and capacitance")
    return normalized


def _normalize_row_values(row: dict[str, str | None]) -> dict[str, float]:
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
    return normalized


def _canonical_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    aliases = {
        "v": "voltage",
        "voltage_v": "voltage",
        "bias": "voltage",
        "bias_voltage": "voltage",
        "ne": "n_eff",
        "n_e": "n_eff",
        "neff": "n_eff",
        "n_eff": "n_eff",
        "effective_index": "n_eff",
        "ng": "n_group",
        "n_g": "n_group",
        "group_index": "n_group",
        "loss": "loss_db_per_cm",
        "loss_db_cm": "loss_db_per_cm",
        "loss_db_per_cm": "loss_db_per_cm",
        "loss_db_per_centimeter": "loss_db_per_cm",
        "capacitance": "capacitance_f",
        "capacitance_f": "capacitance_f",
        "capacitance_ff": "capacitance_ff",
        "capacitance_pf": "capacitance_pf",
        "junction_current": "junction_current_a",
        "junction_current_a": "junction_current_a",
        "current_a": "junction_current_a",
    }
    return aliases.get(normalized, normalized)
