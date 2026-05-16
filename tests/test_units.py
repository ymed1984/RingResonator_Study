import pytest

from ringresonator_study.units import (
    optical_frequency_hz,
    quality_factor,
    wavelength_detuning_to_frequency_ghz,
    wavelength_fsr_to_frequency_fsr_hz,
    wavelength_shift_to_frequency_shift_ghz,
    wavelength_shift_to_frequency_shift_hz,
)


def test_optical_frequency_hz_for_1550_nm():
    assert optical_frequency_hz(1.55) == pytest.approx(193.414489e12, rel=1e-6)


def test_positive_wavelength_shift_is_negative_frequency_shift():
    shift_hz = wavelength_shift_to_frequency_shift_hz(
        center_wavelength_um=1.55,
        delta_wavelength_um=0.001,
    )

    assert shift_hz < 0


def test_wavelength_shift_to_frequency_shift_ghz():
    shift_ghz = wavelength_shift_to_frequency_shift_ghz(
        center_wavelength_um=1.55,
        delta_wavelength_um=0.001,
    )

    assert shift_ghz == pytest.approx(-124.783541, rel=1e-6)


def test_wavelength_fsr_to_frequency_fsr_hz_is_positive():
    fsr_hz = wavelength_fsr_to_frequency_fsr_hz(
        center_wavelength_um=1.55,
        wavelength_fsr_um=0.001,
    )

    assert fsr_hz == pytest.approx(124.783541e9, rel=1e-6)


def test_wavelength_detuning_to_frequency_ghz():
    detuning_ghz = wavelength_detuning_to_frequency_ghz(
        center_wavelength_um=1.55,
        wavelength_um=1.551,
    )

    assert detuning_ghz == pytest.approx(-124.783541, rel=1e-6)


def test_quality_factor_from_wavelength_linewidth():
    assert quality_factor(center_wavelength_um=1.55, linewidth_um=0.001) == 1550


def test_unit_helpers_reject_non_positive_values():
    with pytest.raises(ValueError):
        optical_frequency_hz(0.0)
    with pytest.raises(ValueError):
        quality_factor(center_wavelength_um=1.55, linewidth_um=0.0)
