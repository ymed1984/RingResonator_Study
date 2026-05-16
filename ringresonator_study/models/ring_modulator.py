"""Voltage-dependent single-ring modulator model."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Iterable

from ringresonator_study.models.add_drop import AddDropRing
from ringresonator_study.modulation.metrics import (
    ModulationMetrics,
    calculate_modulation_metrics,
)
from ringresonator_study.modulation.voltage_models import VoltageOpticalModel
from ringresonator_study.responses import AddDropResponse


@dataclass(frozen=True)
class RingModulator:
    """Single-ring modulator built from a passive add-drop ring."""

    ring: AddDropRing
    voltage_model: VoltageOpticalModel
    length_um: float

    def __post_init__(self) -> None:
        if self.length_um <= 0:
            raise ValueError("length_um must be positive")

    def response_for_voltage(
        self,
        wavelength_um: float,
        voltage: float,
    ) -> AddDropResponse:
        """Return optical response for one wavelength and voltage bias."""

        state = self.voltage_model.state_for_voltage(voltage, length_um=self.length_um)
        biased_ring = replace(self.ring, alpha=state.alpha)
        return biased_ring.response_for_wavelength(
            wavelength_um,
            n_eff=state.n_eff,
            length=self.length_um,
        )

    def spectrum_for_voltage(
        self,
        wavelengths_um: Iterable[float],
        voltage: float,
    ) -> list[dict[str, float]]:
        """Return wavelength spectrum for one voltage bias."""

        rows: list[dict[str, float]] = []
        state = self.voltage_model.state_for_voltage(voltage, length_um=self.length_um)
        biased_ring = replace(self.ring, alpha=state.alpha)
        for wavelength_um in wavelengths_um:
            response = biased_ring.response_for_wavelength(
                wavelength_um,
                n_eff=state.n_eff,
                length=self.length_um,
            )
            rows.append(_response_row(wavelength_um, voltage, response, state.alpha))
        return rows

    def transfer_curve(
        self,
        voltages: Iterable[float],
        *,
        wavelength_um: float,
    ) -> list[dict[str, float]]:
        """Return voltage sweep at one wavelength."""

        rows: list[dict[str, float]] = []
        for voltage in voltages:
            response = self.response_for_voltage(wavelength_um, voltage)
            state = self.voltage_model.state_for_voltage(
                voltage,
                length_um=self.length_um,
            )
            rows.append(_response_row(wavelength_um, voltage, response, state.alpha))
        return rows

    def bias_spectrum(
        self,
        wavelengths_um: Iterable[float],
        voltages: Iterable[float],
    ) -> list[dict[str, float]]:
        """Return spectra for multiple voltage biases."""

        wavelengths_um = list(wavelengths_um)
        rows: list[dict[str, float]] = []
        for voltage in voltages:
            rows.extend(self.spectrum_for_voltage(wavelengths_um, voltage))
        return rows

    def metrics(
        self,
        *,
        wavelength_um: float,
        voltage_low: float,
        voltage_high: float,
        port: str = "through",
    ) -> ModulationMetrics:
        """Return static modulation metrics between two voltage biases."""

        low_response = self.response_for_voltage(wavelength_um, voltage_low)
        high_response = self.response_for_voltage(wavelength_um, voltage_high)
        return calculate_modulation_metrics(
            low_response,
            high_response,
            wavelength=wavelength_um,
            voltage_low=voltage_low,
            voltage_high=voltage_high,
            port=port,
        )


def _response_row(
    wavelength_um: float,
    voltage: float,
    response: AddDropResponse,
    alpha: float,
) -> dict[str, float]:
    through_power = response.through.power
    drop_power = response.drop.power
    return {
        "wavelength": wavelength_um,
        "wavelength_um": wavelength_um,
        "voltage": voltage,
        "alpha": alpha,
        "through_power": through_power,
        "through_transmission_db": _power_db(through_power),
        "through_phase": response.through.phase,
        "drop_power": drop_power,
        "drop_transmission_db": _power_db(drop_power),
        "drop_phase": response.drop.phase,
    }


def _power_db(power: float) -> float:
    if power < 0:
        raise ValueError("power must be non-negative")
    if power == 0:
        return -math.inf
    return 10 * math.log10(power)
