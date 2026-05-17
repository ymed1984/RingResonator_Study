"""Electrical RC helpers for voltage-driven ring modulators."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ringresonator_study.modulation.voltage_models import VoltageOpticalModel


@dataclass(frozen=True)
class RCElectricalState:
    """Small-signal RC state at one bias voltage."""

    voltage: float
    resistance_ohm: float
    capacitance_f: float
    time_constant_s: float
    bandwidth_hz: float
    bandwidth_ghz: float


def rc_time_constant_s(*, resistance_ohm: float, capacitance_f: float) -> float:
    """Return RC time constant."""

    _validate_positive("resistance_ohm", resistance_ohm)
    _validate_positive("capacitance_f", capacitance_f)
    return resistance_ohm * capacitance_f


def rc_3db_bandwidth_hz(*, resistance_ohm: float, capacitance_f: float) -> float:
    """Return first-order RC 3 dB bandwidth."""

    tau = rc_time_constant_s(
        resistance_ohm=resistance_ohm,
        capacitance_f=capacitance_f,
    )
    return 1 / (2 * math.pi * tau)


def rc_lowpass_magnitude(
    frequency_hz: float,
    *,
    resistance_ohm: float,
    capacitance_f: float,
) -> float:
    """Return first-order RC low-pass magnitude at frequency."""

    if frequency_hz < 0:
        raise ValueError("frequency_hz must be non-negative")
    tau = rc_time_constant_s(
        resistance_ohm=resistance_ohm,
        capacitance_f=capacitance_f,
    )
    return 1 / math.sqrt(1 + (2 * math.pi * frequency_hz * tau) ** 2)


def rc_state_for_voltage(
    voltage_model: VoltageOpticalModel,
    *,
    voltage: float,
    length_um: float,
    resistance_ohm: float,
) -> RCElectricalState:
    """Return capacitance-derived RC state for one voltage."""

    state = voltage_model.state_for_voltage(voltage, length_um=length_um)
    if state.capacitance_f is None:
        raise ValueError("voltage model state does not include capacitance_f")
    bandwidth_hz = rc_3db_bandwidth_hz(
        resistance_ohm=resistance_ohm,
        capacitance_f=state.capacitance_f,
    )
    return RCElectricalState(
        voltage=voltage,
        resistance_ohm=resistance_ohm,
        capacitance_f=state.capacitance_f,
        time_constant_s=rc_time_constant_s(
            resistance_ohm=resistance_ohm,
            capacitance_f=state.capacitance_f,
        ),
        bandwidth_hz=bandwidth_hz,
        bandwidth_ghz=bandwidth_hz / 1e9,
    )


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
