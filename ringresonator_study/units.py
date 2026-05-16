"""Unit helpers for wavelength- and frequency-domain calculations."""

from __future__ import annotations

SPEED_OF_LIGHT_M_PER_S = 299_792_458.0


def optical_frequency_hz(wavelength_um: float) -> float:
    """Return optical frequency for a vacuum wavelength in micrometers."""

    _validate_positive("wavelength_um", wavelength_um)
    return SPEED_OF_LIGHT_M_PER_S / (wavelength_um * 1e-6)


def wavelength_shift_to_frequency_shift_hz(
    *,
    center_wavelength_um: float,
    delta_wavelength_um: float,
) -> float:
    """Convert a small wavelength shift to frequency shift using ``df/dlambda``."""

    _validate_positive("center_wavelength_um", center_wavelength_um)
    center_wavelength_m = center_wavelength_um * 1e-6
    delta_wavelength_m = delta_wavelength_um * 1e-6
    return -(SPEED_OF_LIGHT_M_PER_S / center_wavelength_m**2) * delta_wavelength_m


def wavelength_shift_to_frequency_shift_ghz(
    *,
    center_wavelength_um: float,
    delta_wavelength_um: float,
) -> float:
    """Convert a small wavelength shift to frequency shift in GHz."""

    return (
        wavelength_shift_to_frequency_shift_hz(
            center_wavelength_um=center_wavelength_um,
            delta_wavelength_um=delta_wavelength_um,
        )
        / 1e9
    )


def wavelength_fsr_to_frequency_fsr_hz(
    *,
    center_wavelength_um: float,
    wavelength_fsr_um: float,
) -> float:
    """Convert a wavelength-domain FSR to an approximate frequency-domain FSR."""

    _validate_positive("wavelength_fsr_um", wavelength_fsr_um)
    return abs(
        wavelength_shift_to_frequency_shift_hz(
            center_wavelength_um=center_wavelength_um,
            delta_wavelength_um=wavelength_fsr_um,
        )
    )


def wavelength_detuning_to_frequency_ghz(
    *,
    center_wavelength_um: float,
    wavelength_um: float,
) -> float:
    """Return frequency detuning for ``wavelength_um`` relative to a center."""

    _validate_positive("wavelength_um", wavelength_um)
    return wavelength_shift_to_frequency_shift_ghz(
        center_wavelength_um=center_wavelength_um,
        delta_wavelength_um=wavelength_um - center_wavelength_um,
    )


def quality_factor(*, center_wavelength_um: float, linewidth_um: float) -> float:
    """Return optical quality factor ``Q = lambda0 / delta_lambda``."""

    _validate_positive("center_wavelength_um", center_wavelength_um)
    _validate_positive("linewidth_um", linewidth_um)
    return center_wavelength_um / linewidth_um


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
