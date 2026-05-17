"""Design sweep helpers for ring modulator studies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ringresonator_study.modulation.operating_point import (
    OperatingPoint,
    find_best_operating_point,
)
from ringresonator_study.modulation.voltage_models import VoltageOpticalModel


@dataclass(frozen=True)
class RingDesignCandidate:
    """Passive ring parameters to evaluate in a design sweep."""

    through_t: float
    length_um: float
    alpha: float = 1.0


@dataclass(frozen=True)
class DesignSweepResult:
    """Best operating point for one passive ring design."""

    through_t: float
    length_um: float
    alpha: float
    best: OperatingPoint

    @property
    def score(self) -> float:
        return self.best.score

    def as_dict(self) -> dict[str, float]:
        return {
            "through_t": self.through_t,
            "length_um": self.length_um,
            "alpha": self.alpha,
            "best_wavelength": self.best.wavelength,
            "best_bias_voltage": self.best.bias_voltage,
            "voltage_low": self.best.voltage_low,
            "voltage_high": self.best.voltage_high,
            "extinction_ratio_db": self.best.extinction_ratio_db,
            "insertion_loss_db": self.best.insertion_loss_db,
            "optical_modulation_amplitude": self.best.optical_modulation_amplitude,
            "score": self.best.score,
        }


def sweep_ring_designs(
    voltage_model: VoltageOpticalModel,
    candidates: Iterable[RingDesignCandidate],
    *,
    wavelengths_um: Iterable[float],
    bias_voltages: Iterable[float],
    drive_voltage: float,
    port: str = "through",
    max_insertion_loss_db: float | None = None,
    min_extinction_ratio_db: float | None = None,
) -> list[DesignSweepResult]:
    """Evaluate best operating point for each ring design candidate."""

    wavelengths_um = list(wavelengths_um)
    bias_voltages = list(bias_voltages)
    results: list[DesignSweepResult] = []
    for candidate in candidates:
        modulator = _modulator_for_candidate(voltage_model, candidate)
        best = find_best_operating_point(
            modulator,
            wavelengths_um=wavelengths_um,
            bias_voltages=bias_voltages,
            drive_voltage=drive_voltage,
            port=port,
            max_insertion_loss_db=max_insertion_loss_db,
            min_extinction_ratio_db=min_extinction_ratio_db,
        )
        results.append(
            DesignSweepResult(
                through_t=candidate.through_t,
                length_um=candidate.length_um,
                alpha=candidate.alpha,
                best=best,
            )
        )
    return sorted(results, key=lambda result: result.score, reverse=True)


def _modulator_for_candidate(
    voltage_model: VoltageOpticalModel,
    candidate: RingDesignCandidate,
):
    from ringresonator_study.components import Coupler
    from ringresonator_study.models.add_drop import AddDropRing
    from ringresonator_study.models.ring_modulator import RingModulator

    if candidate.length_um <= 0:
        raise ValueError("candidate length_um must be positive")
    if candidate.alpha < 0:
        raise ValueError("candidate alpha must be non-negative")
    coupler = Coupler.lossless_from_t(candidate.through_t)
    return RingModulator(
        ring=AddDropRing(
            input_coupler=coupler,
            output_coupler=coupler,
            alpha=candidate.alpha,
        ),
        voltage_model=voltage_model,
        length_um=candidate.length_um,
    )
