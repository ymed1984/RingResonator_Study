import math

import pytest

from ringresonator_study import AddDropRing, Coupler, RingModulator
from ringresonator_study.modulation import LinearVoltageOpticalModel, TableVoltageOpticalModel


def build_modulator() -> RingModulator:
    return RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=LinearVoltageOpticalModel(
            n_eff0=2.4,
            dn_eff_dv=-1e-3,
            loss_db_per_cm0=2.0,
            dloss_db_per_cm_dv=0.5,
        ),
    )


def test_response_for_voltage_changes_with_bias():
    modulator = build_modulator()

    low = modulator.response_for_voltage(1.55, 0.0)
    high = modulator.response_for_voltage(1.55, 1.0)

    assert low.through.power != pytest.approx(high.through.power)


def test_spectrum_for_voltage_returns_rows_with_db_columns():
    modulator = build_modulator()

    rows = modulator.spectrum_for_voltage([1.54, 1.55], 0.5)

    assert len(rows) == 2
    assert rows[0]["voltage"] == pytest.approx(0.5)
    assert "through_transmission_db" in rows[0]
    assert "drop_transmission_db" in rows[0]


def test_bias_spectrum_overlays_wavelength_and_voltage_sweeps():
    modulator = build_modulator()

    rows = modulator.bias_spectrum([1.54, 1.55], [0.0, 1.0, 2.0])

    assert len(rows) == 6
    assert {row["voltage"] for row in rows} == {0.0, 1.0, 2.0}


def test_bias_spectrum_accepts_wavelength_generators():
    modulator = build_modulator()
    wavelengths = (wavelength for wavelength in [1.54, 1.55])

    rows = modulator.bias_spectrum(wavelengths, [0.0, 1.0])

    assert len(rows) == 4


def test_transfer_curve_returns_one_row_per_voltage():
    modulator = build_modulator()

    rows = modulator.transfer_curve([0.0, 0.5, 1.0], wavelength_um=1.55)

    assert [row["voltage"] for row in rows] == [0.0, 0.5, 1.0]


def test_ring_modulator_combines_intrinsic_and_voltage_alpha():
    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=0.9,
        ),
        length_um=30.0,
        voltage_model=LinearVoltageOpticalModel(
            n_eff0=2.4,
            dn_eff_dv=0.0,
            loss_db_per_cm0=2.0,
        ),
    )

    state = modulator.voltage_model.state_for_voltage(0.0, length_um=30.0)
    rows = modulator.spectrum_for_voltage([1.55], 0.0)

    assert rows[0]["alpha"] == pytest.approx(0.9 * state.alpha)


def test_metrics_returns_static_modulation_values():
    modulator = build_modulator()

    metrics = modulator.metrics(
        wavelength_um=1.55,
        voltage_low=0.0,
        voltage_high=1.0,
        port="through",
    )

    assert metrics.extinction_ratio_db >= 0.0
    assert math.isfinite(metrics.insertion_loss_db)
    assert metrics.optical_modulation_amplitude >= 0.0


def test_ring_modulator_accepts_table_voltage_model():
    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=TableVoltageOpticalModel(
            rows=[
                {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
                {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
            ]
        ),
    )

    response = modulator.response_for_voltage(1.55, 0.5)

    assert response.through.power >= 0.0
