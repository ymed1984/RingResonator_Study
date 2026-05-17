"""Helpers for extracting resonance shifts from bias spectra."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ringresonator_study.units import (
    quality_factor,
    wavelength_fsr_to_frequency_fsr_hz,
)


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


def extract_resonance_metrics(
    rows: Iterable[dict[str, float]],
    *,
    port: str = "through",
    mode: str = "min",
) -> list[dict[str, float]]:
    """Return resonance position, linewidth, Q, and contrast for each voltage."""

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
        voltage_rows = sorted(grouped[voltage], key=lambda row: row["wavelength"])
        powers = [row[power_key] for row in voltage_rows]
        wavelengths = [row["wavelength"] for row in voltage_rows]

        selector = min if mode == "min" else max
        resonance_row = selector(voltage_rows, key=lambda row: row[power_key])
        resonance_power = resonance_row[power_key]
        baseline_power = max(powers) if mode == "min" else min(powers)
        half_level = (baseline_power + resonance_power) / 2
        left, right = _half_level_crossings(
            wavelengths,
            powers,
            resonance_index=voltage_rows.index(resonance_row),
            half_level=half_level,
        )
        linewidth_um = right - left if math.isfinite(left) and math.isfinite(right) else math.nan
        q_loaded = (
            quality_factor(
                center_wavelength_um=resonance_row["wavelength"],
                linewidth_um=linewidth_um,
            )
            if math.isfinite(linewidth_um) and linewidth_um > 0
            else math.nan
        )
        linewidth_ghz = (
            wavelength_fsr_to_frequency_fsr_hz(
                center_wavelength_um=resonance_row["wavelength"],
                wavelength_fsr_um=linewidth_um,
            )
            / 1e9
            if math.isfinite(linewidth_um) and linewidth_um > 0
            else math.nan
        )
        results.append(
            {
                "voltage": voltage,
                "resonance_wavelength": resonance_row["wavelength"],
                "power": resonance_power,
                "transmission_db": resonance_row.get(
                    db_key,
                    _power_db(resonance_power),
                ),
                "baseline_power": baseline_power,
                "half_level_power": half_level,
                "linewidth_um": linewidth_um,
                "linewidth_pm": linewidth_um * 1e6,
                "linewidth_ghz": linewidth_ghz,
                "quality_factor": q_loaded,
                "contrast_db": _contrast_db(
                    resonance_power=resonance_power,
                    baseline_power=baseline_power,
                    mode=mode,
                ),
            }
        )
    return results


def _group_by_voltage(
    rows: Iterable[dict[str, float]],
) -> dict[float, list[dict[str, float]]]:
    grouped: dict[float, list[dict[str, float]]] = {}
    for row in rows:
        grouped.setdefault(row["voltage"], []).append(row)
    return grouped


def _half_level_crossings(
    wavelengths: list[float],
    powers: list[float],
    *,
    resonance_index: int,
    half_level: float,
) -> tuple[float, float]:
    left = math.nan
    for index in range(resonance_index - 1, -1, -1):
        if _brackets_half_level(powers[index], powers[index + 1], half_level):
            left = _linear_crossing(
                wavelengths[index],
                powers[index],
                wavelengths[index + 1],
                powers[index + 1],
                half_level,
            )
            break

    right = math.nan
    for index in range(resonance_index, len(powers) - 1):
        if _brackets_half_level(powers[index], powers[index + 1], half_level):
            right = _linear_crossing(
                wavelengths[index],
                powers[index],
                wavelengths[index + 1],
                powers[index + 1],
                half_level,
            )
            break
    return left, right


def _brackets_half_level(power_a: float, power_b: float, half_level: float) -> bool:
    return (power_a - half_level) * (power_b - half_level) <= 0 and power_a != power_b


def _linear_crossing(
    wavelength_a: float,
    power_a: float,
    wavelength_b: float,
    power_b: float,
    half_level: float,
) -> float:
    fraction = (half_level - power_a) / (power_b - power_a)
    return wavelength_a + fraction * (wavelength_b - wavelength_a)


def _contrast_db(*, resonance_power: float, baseline_power: float, mode: str) -> float:
    if mode == "min":
        return _ratio_db(baseline_power, resonance_power)
    return _ratio_db(resonance_power, baseline_power)


def _power_db(power: float) -> float:
    if power < 0:
        raise ValueError("power must be non-negative")
    if power == 0:
        return -math.inf
    return 10 * math.log10(power)


def _ratio_db(numerator: float, denominator: float) -> float:
    if numerator < 0 or denominator < 0:
        raise ValueError("powers must be non-negative")
    if denominator == 0:
        return math.inf
    if numerator == 0:
        return -math.inf
    return 10 * math.log10(numerator / denominator)
