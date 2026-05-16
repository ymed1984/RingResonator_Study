"""Helpers for extracting resonance shifts from bias spectra."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class ResonancePoint:
    """Detected resonance point for one voltage bias."""

    voltage: float
    resonance_wavelength: float
    power: float
    transmission_db: float


def track_resonance(
    rows: Iterable[dict[str, float]],
    *,
    port: str = "through",
    mode: str = "min",
) -> list[dict[str, float]]:
    """Track the minimum or maximum transmission point for each voltage."""

    if port not in {"through", "drop"}:
        raise ValueError("port must be 'through' or 'drop'")
    if mode not in {"min", "max"}:
        raise ValueError("mode must be 'min' or 'max'")

    grouped = _group_by_voltage(rows)
    if not grouped:
        raise ValueError("rows must not be empty")

    power_key = f"{port}_power"
    db_key = f"{port}_transmission_db"
    results = []
    for voltage in sorted(grouped):
        voltage_rows = grouped[voltage]
        selector = min if mode == "min" else max
        row = selector(voltage_rows, key=lambda item: item[power_key])
        power = row[power_key]
        results.append(
            {
                "voltage": voltage,
                "resonance_wavelength": row["wavelength"],
                "power": power,
                "transmission_db": row.get(db_key, _power_db(power)),
            }
        )
    return results


def resonance_shifts(
    resonances: Iterable[dict[str, float]],
    *,
    reference_voltage: float | None = None,
) -> list[dict[str, float]]:
    """Return wavelength shifts relative to a reference resonance."""

    resonances = sorted(resonances, key=lambda row: row["voltage"])
    if not resonances:
        raise ValueError("resonances must not be empty")

    if reference_voltage is None:
        reference = resonances[0]
    else:
        matches = [row for row in resonances if row["voltage"] == reference_voltage]
        if not matches:
            raise ValueError("reference_voltage was not found in resonances")
        reference = matches[0]

    reference_wavelength = reference["resonance_wavelength"]
    return [
        {
            **row,
            "delta_wavelength_um": row["resonance_wavelength"] - reference_wavelength,
            "delta_wavelength_pm": (row["resonance_wavelength"] - reference_wavelength)
            * 1e6,
        }
        for row in resonances
    ]


def _group_by_voltage(
    rows: Iterable[dict[str, float]],
) -> dict[float, list[dict[str, float]]]:
    grouped: dict[float, list[dict[str, float]]] = {}
    for row in rows:
        grouped.setdefault(row["voltage"], []).append(row)
    return grouped


def _power_db(power: float) -> float:
    if power < 0:
        raise ValueError("power must be non-negative")
    if power == 0:
        return -math.inf
    return 10 * math.log10(power)
