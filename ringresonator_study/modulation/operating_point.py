"""Operating-point analysis for voltage-driven ring modulators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from ringresonator_study.modulation.metrics import ModulationMetrics


class ModulatorMetricsModel(Protocol):
    """Protocol for objects that can evaluate static modulation metrics."""

    def metrics(
        self,
        *,
        wavelength_um: float,
        voltage_low: float,
        voltage_high: float,
        port: str = "through",
    ) -> ModulationMetrics:
        """Return metrics for two voltage states."""


@dataclass(frozen=True)
class OperatingPoint:
    """Evaluated modulator operating point."""

    wavelength: float
    bias_voltage: float
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
    score: float


def analyze_operating_points(
    modulator: ModulatorMetricsModel,
    wavelengths_um: Iterable[float],
    bias_voltages: Iterable[float],
    *,
    drive_voltage: float,
    port: str = "through",
    skip_invalid: bool = True,
) -> list[OperatingPoint]:
    """Evaluate all wavelength/bias candidates for a voltage swing."""

    if drive_voltage <= 0:
        raise ValueError("drive_voltage must be positive")
    if port not in {"through", "drop"}:
        raise ValueError("port must be 'through' or 'drop'")

    points: list[OperatingPoint] = []
    half_drive = drive_voltage / 2
    for wavelength_um in wavelengths_um:
        if wavelength_um <= 0:
            raise ValueError("wavelengths_um must contain only positive values")
        for bias_voltage in bias_voltages:
            voltage_low = bias_voltage - half_drive
            voltage_high = bias_voltage + half_drive
            try:
                metrics = modulator.metrics(
                    wavelength_um=wavelength_um,
                    voltage_low=voltage_low,
                    voltage_high=voltage_high,
                    port=port,
                )
            except ValueError:
                if skip_invalid:
                    continue
                raise
            points.append(_operating_point(wavelength_um, bias_voltage, metrics))

    if not points:
        raise ValueError("no valid operating points were evaluated")
    return points


def rank_operating_points(
    points: Iterable[OperatingPoint],
    *,
    max_insertion_loss_db: float | None = None,
    min_extinction_ratio_db: float | None = None,
    limit: int | None = None,
) -> list[OperatingPoint]:
    """Filter and rank operating points by score."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")

    filtered = list(points)
    if max_insertion_loss_db is not None:
        filtered = [
            point
            for point in filtered
            if point.insertion_loss_db <= max_insertion_loss_db
        ]
    if min_extinction_ratio_db is not None:
        filtered = [
            point
            for point in filtered
            if point.extinction_ratio_db >= min_extinction_ratio_db
        ]

    ranked = sorted(filtered, key=lambda point: point.score, reverse=True)
    if limit is not None:
        return ranked[:limit]
    return ranked


def find_best_operating_point(
    modulator: ModulatorMetricsModel,
    wavelengths_um: Iterable[float],
    bias_voltages: Iterable[float],
    *,
    drive_voltage: float,
    port: str = "through",
    max_insertion_loss_db: float | None = None,
    min_extinction_ratio_db: float | None = None,
    skip_invalid: bool = True,
) -> OperatingPoint:
    """Return the highest-scoring operating point that passes constraints."""

    points = analyze_operating_points(
        modulator,
        wavelengths_um,
        bias_voltages,
        drive_voltage=drive_voltage,
        port=port,
        skip_invalid=skip_invalid,
    )
    ranked = rank_operating_points(
        points,
        max_insertion_loss_db=max_insertion_loss_db,
        min_extinction_ratio_db=min_extinction_ratio_db,
        limit=1,
    )
    if not ranked:
        raise ValueError("no operating point satisfies the constraints")
    return ranked[0]


def _operating_point(
    wavelength_um: float,
    bias_voltage: float,
    metrics: ModulationMetrics,
) -> OperatingPoint:
    score = metrics.extinction_ratio_db - metrics.insertion_loss_db
    return OperatingPoint(
        wavelength=wavelength_um,
        bias_voltage=bias_voltage,
        voltage_low=metrics.voltage_low,
        voltage_high=metrics.voltage_high,
        port=metrics.port,
        low_power=metrics.low_power,
        high_power=metrics.high_power,
        on_power=metrics.on_power,
        off_power=metrics.off_power,
        extinction_ratio_db=metrics.extinction_ratio_db,
        insertion_loss_db=metrics.insertion_loss_db,
        optical_modulation_amplitude=metrics.optical_modulation_amplitude,
        score=score,
    )
