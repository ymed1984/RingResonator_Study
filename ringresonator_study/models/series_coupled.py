"""Series-coupled CROW filter model.

This module follows the compact-model structure used in the Ansys/Lumerical
Tunable CROW Filter example: identical rings are coupled in series, the first and
last rings couple to bus waveguides with ``kappa1``, and adjacent rings couple to
each other with ``kappa2``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np

from ringresonator_study.responses import PortResponse, ThroughDropResponse

SPEED_OF_LIGHT_M_PER_S = 299_792_458.0


@dataclass(frozen=True)
class CROWDesign:
    """Key physical design values for a CROW filter."""

    ring_count: int
    radius_um: float
    fsr_hz: float
    fsr_ghz: float
    round_trip_time_s: float
    center_wavelength_um: float
    kappa1_power: float
    kappa2_power: float
    loss_db_per_cm: float


@dataclass(frozen=True)
class SeriesCoupledRings:
    """Coupled-resonator optical waveguide (CROW) filter.

    Args:
        ring_count: Number of identical rings in the CROW chain.
        kappa1_power: Power coupling coefficient between bus waveguides and the
            edge rings. This corresponds to ``kappa1_squared`` in the Ansys
            compact-model example.
        kappa2_power: Power coupling coefficient between adjacent rings. This
            corresponds to ``kappa2_squared`` in the Ansys compact-model example.
        radius_um: Ring radius in micrometers.
        n_eff: Effective index used for phase.
        n_group: Group index used for FSR and round-trip time.
        center_wavelength_um: Nominal resonance wavelength.
        loss_db_per_cm: Waveguide propagation loss.
        tuning_efficiency_nm_per_v2: Thermal tuning coefficient.
        tuning_voltages: Per-ring thermal tuning voltage. If one value is given,
            it is applied to all rings.
        ring_wavelength_offsets_um: Optional static per-ring resonance offsets.
    """

    ring_count: int
    kappa1_power: float
    kappa2_power: float
    radius_um: float
    n_eff: float
    n_group: float
    center_wavelength_um: float = 1.55
    loss_db_per_cm: float = 1.0
    tuning_efficiency_nm_per_v2: float = 0.1
    tuning_voltages: tuple[float, ...] = (0.0,)
    ring_wavelength_offsets_um: tuple[float, ...] = (0.0,)

    @classmethod
    def ansys_nominal_two_ring(
        cls,
        *,
        center_wavelength_um: float = 1.55,
        n_eff: float = 2.566,
        n_group: float = 3.893,
        fsr_hz: float = 79.5e9,
        kappa1_power: float = 0.13,
        kappa2_power: float = 0.0047,
        loss_db_per_cm: float = 1.0,
        tuning_voltage: float = 0.0,
    ) -> "SeriesCoupledRings":
        """Build the nominal two-ring CROW from the Ansys example values."""

        return cls(
            ring_count=2,
            kappa1_power=kappa1_power,
            kappa2_power=kappa2_power,
            radius_um=radius_for_fsr(fsr_hz=fsr_hz, n_group=n_group),
            n_eff=n_eff,
            n_group=n_group,
            center_wavelength_um=center_wavelength_um,
            loss_db_per_cm=loss_db_per_cm,
            tuning_voltages=(tuning_voltage, tuning_voltage),
        )

    @classmethod
    def from_fsr(
        cls,
        *,
        ring_count: int,
        fsr_hz: float,
        kappa1_power: float,
        kappa2_power: float,
        n_eff: float,
        n_group: float,
        center_wavelength_um: float = 1.55,
        loss_db_per_cm: float = 1.0,
    ) -> "SeriesCoupledRings":
        return cls(
            ring_count=ring_count,
            kappa1_power=kappa1_power,
            kappa2_power=kappa2_power,
            radius_um=radius_for_fsr(fsr_hz=fsr_hz, n_group=n_group),
            n_eff=n_eff,
            n_group=n_group,
            center_wavelength_um=center_wavelength_um,
            loss_db_per_cm=loss_db_per_cm,
        )

    def __post_init__(self) -> None:
        if self.ring_count < 1:
            raise ValueError("ring_count must be positive")
        _validate_power_coupling("kappa1_power", self.kappa1_power)
        _validate_power_coupling("kappa2_power", self.kappa2_power)
        if self.radius_um <= 0:
            raise ValueError("radius_um must be positive")
        if self.n_eff <= 0 or self.n_group <= 0:
            raise ValueError("n_eff and n_group must be positive")
        if self.loss_db_per_cm < 0:
            raise ValueError("loss_db_per_cm must be non-negative")

        object.__setattr__(
            self,
            "tuning_voltages",
            _expand_to_ring_count(self.tuning_voltages, self.ring_count, "tuning_voltages"),
        )
        object.__setattr__(
            self,
            "ring_wavelength_offsets_um",
            _expand_to_ring_count(
                self.ring_wavelength_offsets_um,
                self.ring_count,
                "ring_wavelength_offsets_um",
            ),
        )

    @property
    def design(self) -> CROWDesign:
        fsr_hz = self.fsr_hz
        return CROWDesign(
            ring_count=self.ring_count,
            radius_um=self.radius_um,
            fsr_hz=fsr_hz,
            fsr_ghz=fsr_hz / 1e9,
            round_trip_time_s=self.round_trip_time_s,
            center_wavelength_um=self.center_wavelength_um,
            kappa1_power=self.kappa1_power,
            kappa2_power=self.kappa2_power,
            loss_db_per_cm=self.loss_db_per_cm,
        )

    @property
    def circumference_um(self) -> float:
        return 2 * math.pi * self.radius_um

    @property
    def round_trip_time_s(self) -> float:
        length_m = self.circumference_um * 1e-6
        return self.n_group * length_m / SPEED_OF_LIGHT_M_PER_S

    @property
    def fsr_hz(self) -> float:
        return 1 / self.round_trip_time_s

    @property
    def round_trip_field_alpha(self) -> float:
        length_cm = self.circumference_um * 1e-4
        return 10 ** (-(self.loss_db_per_cm * length_cm) / 20)

    def resonance_wavelengths_um(self) -> tuple[float, ...]:
        tuning_shift_um = tuple(
            voltage**2 * self.tuning_efficiency_nm_per_v2 * 1e-3
            for voltage in self.tuning_voltages
        )
        return tuple(
            self.center_wavelength_um + offset + tuning
            for offset, tuning in zip(
                self.ring_wavelength_offsets_um,
                tuning_shift_um,
                strict=True,
            )
        )

    def response_for_wavelength(self, wavelength_um: float) -> ThroughDropResponse:
        """Return through/drop response at one wavelength."""

        amplitudes = self._solve_modal_amplitudes(wavelength_um)
        gamma_bus = self._bus_decay_rate()
        through = 1 - 1j * math.sqrt(2 * gamma_bus) * amplitudes[0]
        drop = -1j * math.sqrt(2 * gamma_bus) * amplitudes[-1]
        return ThroughDropResponse(
            through=PortResponse(through),
            drop=PortResponse(drop),
        )

    def spectrum(self, wavelengths: Iterable[float]) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for wavelength in wavelengths:
            response = self.response_for_wavelength(wavelength)
            rows.append(
                {
                    "wavelength": wavelength,
                    "through_power": response.through.power,
                    "through_phase": response.through.phase,
                    "drop_power": response.drop.power,
                    "drop_phase": response.drop.phase,
                }
            )
        return rows

    def _solve_modal_amplitudes(self, wavelength_um: float) -> np.ndarray:
        gamma_bus = self._bus_decay_rate()
        gamma_loss = self._intrinsic_decay_rate()
        coupling_rate = self._ring_ring_coupling_rate()

        matrix = np.zeros((self.ring_count, self.ring_count), dtype=complex)
        source = np.zeros(self.ring_count, dtype=complex)
        source[0] = 1j * math.sqrt(2 * gamma_bus)

        detunings = self._angular_detunings(wavelength_um)
        for index, detuning in enumerate(detunings):
            gamma = gamma_loss
            if index == 0:
                gamma += gamma_bus
            if index == self.ring_count - 1:
                gamma += gamma_bus
            matrix[index, index] = -gamma - 1j * detuning

            if index > 0:
                matrix[index, index - 1] = -1j * coupling_rate
            if index < self.ring_count - 1:
                matrix[index, index + 1] = -1j * coupling_rate

        return np.linalg.solve(matrix, source)

    def _angular_detunings(self, wavelength_um: float) -> tuple[float, ...]:
        detunings = []
        length_um = self.circumference_um
        for resonance_wavelength in self.resonance_wavelengths_um():
            phase_delta = 2 * math.pi * self.n_eff * length_um * (
                (1 / wavelength_um) - (1 / resonance_wavelength)
            )
            wrapped_phase_delta = wrap_to_pi(phase_delta)
            detunings.append(-wrapped_phase_delta / self.round_trip_time_s)
        return tuple(detunings)

    def _bus_decay_rate(self) -> float:
        return self.kappa1_power / (2 * self.round_trip_time_s)

    def _ring_ring_coupling_rate(self) -> float:
        return math.sqrt(self.kappa2_power) / self.round_trip_time_s

    def _intrinsic_decay_rate(self) -> float:
        power_loss = 1 - self.round_trip_field_alpha**2
        return power_loss / (2 * self.round_trip_time_s)


def radius_for_fsr(*, fsr_hz: float, n_group: float) -> float:
    """Return the ring radius in micrometers from ``FSR = c / (ng 2*pi*r)``."""

    if fsr_hz <= 0:
        raise ValueError("fsr_hz must be positive")
    if n_group <= 0:
        raise ValueError("n_group must be positive")
    radius_m = SPEED_OF_LIGHT_M_PER_S / (n_group * 2 * math.pi * fsr_hz)
    return radius_m * 1e6


def wrap_to_pi(value: float) -> float:
    return (value + math.pi) % (2 * math.pi) - math.pi


def _validate_power_coupling(name: str, value: float) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1")


def _expand_to_ring_count(
    values: Sequence[float],
    ring_count: int,
    name: str,
) -> tuple[float, ...]:
    if len(values) == 1:
        return tuple(values[0] for _ in range(ring_count))
    if len(values) != ring_count:
        raise ValueError(f"{name} must have length 1 or ring_count")
    return tuple(values)
