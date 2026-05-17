import pytest

from ringresonator_study.modulation import (
    TableVoltageOpticalModel,
    rc_3db_bandwidth_hz,
    rc_lowpass_magnitude,
    rc_state_for_voltage,
    rc_time_constant_s,
)


def test_rc_time_constant_and_bandwidth():
    tau = rc_time_constant_s(resistance_ohm=50.0, capacitance_f=40e-15)
    bandwidth = rc_3db_bandwidth_hz(resistance_ohm=50.0, capacitance_f=40e-15)

    assert tau == pytest.approx(2e-12)
    assert bandwidth == pytest.approx(1 / (2 * 3.141592653589793 * 2e-12))


def test_rc_lowpass_magnitude_at_zero_frequency():
    magnitude = rc_lowpass_magnitude(
        0.0,
        resistance_ohm=50.0,
        capacitance_f=40e-15,
    )

    assert magnitude == pytest.approx(1.0)


def test_rc_state_for_voltage_uses_voltage_model_capacitance():
    model = TableVoltageOpticalModel(
        rows=[
            {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0, "capacitance_f": 40e-15},
            {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0, "capacitance_f": 20e-15},
        ]
    )

    state = rc_state_for_voltage(
        model,
        voltage=0.5,
        length_um=30.0,
        resistance_ohm=50.0,
    )

    assert state.capacitance_f == pytest.approx(30e-15)
    assert state.bandwidth_ghz == pytest.approx(state.bandwidth_hz / 1e9)


def test_rc_state_for_voltage_requires_capacitance():
    model = TableVoltageOpticalModel(
        rows=[
            {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
            {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
        ]
    )

    with pytest.raises(ValueError):
        rc_state_for_voltage(
            model,
            voltage=0.5,
            length_um=30.0,
            resistance_ohm=50.0,
        )
