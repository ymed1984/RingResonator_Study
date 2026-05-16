"""Modulation metrics for voltage-dependent ring responses."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ringresonator_study.responses import AddDropResponse


@dataclass(frozen=True)
class ModulationMetrics:
    """Basic static modulation metrics for two bias points."""

    wavelength: float
    voltage_low: float
    voltage_high: float
    port: str
    low_power: float
    high_power: float
    on_power: float
    off_power: float
    extinction_ratio_db: float
    insertion_loss_db: float
    optical_modulation_amplitude: float


def calculate_modulation_metrics(
    low_response: AddDropResponse,
    high_response: AddDropResponse,
    *,
    wavelength: float,
    voltage_low: float,
    voltage_high: float,
    port: str = "through",
) -> ModulationMetrics:
    """Calculate ER, IL, and OMA for two voltage states."""

    low_power = _power_for_port(low_response, port)
    high_power = _power_for_port(high_response, port)
    on_power = max(low_power, high_power)
    off_power = min(low_power, high_power)
    return ModulationMetrics(
        wavelength=wavelength,
        voltage_low=voltage_low,
        voltage_high=voltage_high,
        port=port,
        low_power=low_power,
        high_power=high_power,
        on_power=on_power,
        off_power=off_power,
        extinction_ratio_db=_ratio_db(on_power, off_power),
        insertion_loss_db=-_power_db(on_power),
        optical_modulation_amplitude=on_power - off_power,
    )


def _power_for_port(response: AddDropResponse, port: str) -> float:
    if port == "through":
        return response.through.power
    if port == "drop":
        return response.drop.power
    raise ValueError("port must be 'through' or 'drop'")


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
