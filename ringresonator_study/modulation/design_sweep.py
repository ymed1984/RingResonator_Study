"""Design sweep helpers for ring modulator studies."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ringresonator_study.modulation.operating_point import (
    OperatingPoint,
    find_best_operating_point,
)
from ringresonator_study.modulation.electrical import rc_state_for_voltage
from ringresonator_study.modulation.voltage_models import VoltageOpticalModel


@dataclass(frozen=True)
class RingDesignCandidate:
    """Passive ring parameters to evaluate in a design sweep."""

    through_t: float
    length_um: float
    alpha: float = 1.0


@dataclass(frozen=True)
class RingModulatorDesignCandidate:
    """Passive single-ring design candidate for modulator design sweeps."""

    input_t: float
    length_um: float
    output_t: float | None = None
    intrinsic_alpha: float = 1.0

    @property
    def effective_output_t(self) -> float:
        """Return output self-coupling, defaulting to a symmetric ring."""

        if self.output_t is None:
            return self.input_t
        return self.output_t


@dataclass(frozen=True)
class RingModulatorDesignSpec:
    """Design-space and scoring settings for single-ring modulator sweeps."""

    candidates: Iterable[RingModulatorDesignCandidate]
    wavelengths_um: Iterable[float]
    bias_voltages: Iterable[float]
    drive_voltage: float
    port: str = "through"
    max_insertion_loss_db: float | None = None
    min_extinction_ratio_db: float | None = None
    min_rc_bandwidth_ghz: float | None = None
    resistance_ohm: float = 50.0
    bandwidth_weight: float = 1.0
    bandwidth_floor_ghz: float = 1e-12
    skip_invalid: bool = True


@dataclass(frozen=True)
class RingModulatorDesignResult:
    """Ranked design result for one single-ring modulator candidate."""

    candidate: RingModulatorDesignCandidate
    best: OperatingPoint
    rc_bandwidth_ghz: float | None
    constraints_passed: bool
    score: float

    def as_dict(self) -> dict[str, float | bool | str | None]:
        """Return a flat row suitable for CSV export or DataFrame creation."""

        return {
            "input_t": self.candidate.input_t,
            "output_t": self.candidate.effective_output_t,
            "length_um": self.candidate.length_um,
            "intrinsic_alpha": self.candidate.intrinsic_alpha,
            "best_wavelength": self.best.wavelength,
            "best_bias_voltage": self.best.bias_voltage,
            "voltage_low": self.best.voltage_low,
            "voltage_high": self.best.voltage_high,
            "port": self.best.port,
            "low_power": self.best.low_power,
            "high_power": self.best.high_power,
            "on_power": self.best.on_power,
            "off_power": self.best.off_power,
            "extinction_ratio_db": self.best.extinction_ratio_db,
            "insertion_loss_db": self.best.insertion_loss_db,
            "optical_modulation_amplitude": self.best.optical_modulation_amplitude,
            "rc_bandwidth_ghz": self.rc_bandwidth_ghz,
            "constraints_passed": self.constraints_passed,
            "score": self.score,
        }


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


def design_ring_modulator(
    voltage_model: VoltageOpticalModel,
    spec: RingModulatorDesignSpec,
) -> list[RingModulatorDesignResult]:
    """Rank single-ring modulator design candidates by optical and RC metrics."""

    _validate_design_spec(spec)
    candidates = list(spec.candidates)
    if not candidates:
        raise ValueError("spec candidates must not be empty")
    for candidate in candidates:
        _validate_design_candidate(candidate)

    wavelengths_um = list(spec.wavelengths_um)
    bias_voltages = list(spec.bias_voltages)
    results: list[RingModulatorDesignResult] = []
    for candidate in candidates:
        try:
            result = _evaluate_design_candidate(
                voltage_model,
                spec,
                candidate,
                wavelengths_um=wavelengths_um,
                bias_voltages=bias_voltages,
            )
        except ValueError:
            if spec.skip_invalid:
                continue
            raise

        if result.constraints_passed:
            results.append(result)

    if not results:
        raise ValueError("no ring modulator design candidate satisfies the constraints")
    return sorted(results, key=lambda result: result.score, reverse=True)


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
    candidates = list(candidates)
    for candidate in candidates:
        _validate_ring_design_candidate(candidate)
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


def _evaluate_design_candidate(
    voltage_model: VoltageOpticalModel,
    spec: RingModulatorDesignSpec,
    candidate: RingModulatorDesignCandidate,
    *,
    wavelengths_um: list[float],
    bias_voltages: list[float],
) -> RingModulatorDesignResult:
    _validate_design_candidate(candidate)
    modulator = _modulator_for_design_candidate(voltage_model, candidate)
    best = find_best_operating_point(
        modulator,
        wavelengths_um=wavelengths_um,
        bias_voltages=bias_voltages,
        drive_voltage=spec.drive_voltage,
        port=spec.port,
        max_insertion_loss_db=spec.max_insertion_loss_db,
        min_extinction_ratio_db=spec.min_extinction_ratio_db,
        skip_invalid=spec.skip_invalid,
    )
    rc_bandwidth_ghz = _rc_bandwidth_for_bias(
        voltage_model,
        voltage=best.bias_voltage,
        length_um=candidate.length_um,
        resistance_ohm=spec.resistance_ohm,
    )
    constraints_passed = _passes_design_constraints(
        best,
        rc_bandwidth_ghz=rc_bandwidth_ghz,
        spec=spec,
    )
    score = _design_score(
        best,
        rc_bandwidth_ghz=rc_bandwidth_ghz,
        bandwidth_weight=spec.bandwidth_weight,
        bandwidth_floor_ghz=spec.bandwidth_floor_ghz,
    )
    return RingModulatorDesignResult(
        candidate=candidate,
        best=best,
        rc_bandwidth_ghz=rc_bandwidth_ghz,
        constraints_passed=constraints_passed,
        score=score,
    )


def _modulator_for_design_candidate(
    voltage_model: VoltageOpticalModel,
    candidate: RingModulatorDesignCandidate,
):
    from ringresonator_study.components import Coupler
    from ringresonator_study.models.add_drop import AddDropRing
    from ringresonator_study.models.ring_modulator import RingModulator

    input_coupler = Coupler.lossless_from_t(candidate.input_t)
    output_coupler = Coupler.lossless_from_t(candidate.effective_output_t)
    return RingModulator(
        ring=AddDropRing(
            input_coupler=input_coupler,
            output_coupler=output_coupler,
            alpha=candidate.intrinsic_alpha,
        ),
        voltage_model=voltage_model,
        length_um=candidate.length_um,
    )


def _validate_ring_design_candidate(candidate: RingDesignCandidate) -> None:
    if candidate.length_um <= 0:
        raise ValueError("candidate length_um must be positive")
    if candidate.alpha < 0:
        raise ValueError("candidate alpha must be non-negative")


def _modulator_for_candidate(
    voltage_model: VoltageOpticalModel,
    candidate: RingDesignCandidate,
):
    from ringresonator_study.components import Coupler
    from ringresonator_study.models.add_drop import AddDropRing
    from ringresonator_study.models.ring_modulator import RingModulator

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


def _validate_design_spec(spec: RingModulatorDesignSpec) -> None:
    if spec.drive_voltage <= 0:
        raise ValueError("spec drive_voltage must be positive")
    if spec.port not in {"through", "drop"}:
        raise ValueError("spec port must be 'through' or 'drop'")
    if spec.resistance_ohm <= 0:
        raise ValueError("spec resistance_ohm must be positive")
    if spec.bandwidth_weight < 0:
        raise ValueError("spec bandwidth_weight must be non-negative")
    if spec.bandwidth_floor_ghz <= 0:
        raise ValueError("spec bandwidth_floor_ghz must be positive")
    if spec.min_rc_bandwidth_ghz is not None and spec.min_rc_bandwidth_ghz < 0:
        raise ValueError("spec min_rc_bandwidth_ghz must be non-negative")


def _validate_design_candidate(candidate: RingModulatorDesignCandidate) -> None:
    if candidate.length_um <= 0:
        raise ValueError("candidate length_um must be positive")
    if candidate.intrinsic_alpha < 0:
        raise ValueError("candidate intrinsic_alpha must be non-negative")


def _rc_bandwidth_for_bias(
    voltage_model: VoltageOpticalModel,
    *,
    voltage: float,
    length_um: float,
    resistance_ohm: float,
) -> float | None:
    try:
        rc_state = rc_state_for_voltage(
            voltage_model,
            voltage=voltage,
            length_um=length_um,
            resistance_ohm=resistance_ohm,
        )
    except ValueError as error:
        if "capacitance_f" in str(error):
            return None
        raise
    return rc_state.bandwidth_ghz


def _passes_design_constraints(
    best: OperatingPoint,
    *,
    rc_bandwidth_ghz: float | None,
    spec: RingModulatorDesignSpec,
) -> bool:
    if (
        spec.max_insertion_loss_db is not None
        and best.insertion_loss_db > spec.max_insertion_loss_db
    ):
        return False
    if (
        spec.min_extinction_ratio_db is not None
        and best.extinction_ratio_db < spec.min_extinction_ratio_db
    ):
        return False
    if spec.min_rc_bandwidth_ghz is not None:
        if rc_bandwidth_ghz is None:
            return False
        if rc_bandwidth_ghz < spec.min_rc_bandwidth_ghz:
            return False
    return True


def _design_score(
    best: OperatingPoint,
    *,
    rc_bandwidth_ghz: float | None,
    bandwidth_weight: float,
    bandwidth_floor_ghz: float,
) -> float:
    score = best.extinction_ratio_db - best.insertion_loss_db
    if rc_bandwidth_ghz is not None:
        score += bandwidth_weight * math.log10(
            max(rc_bandwidth_ghz, bandwidth_floor_ghz)
        )
    return score
