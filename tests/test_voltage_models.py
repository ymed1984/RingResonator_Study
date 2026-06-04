import pytest

from ringresonator_study.modulation import (
    LinearVoltageOpticalModel,
    TableVoltageOpticalModel,
    field_alpha_from_loss_db_per_cm,
)


def test_field_alpha_from_loss_db_per_cm_uses_round_trip_length():
    alpha = field_alpha_from_loss_db_per_cm(2.0, length_um=1000.0)

    assert alpha == pytest.approx(10 ** (-(2.0 * 0.1) / 20))


def test_linear_voltage_model_returns_voltage_dependent_state():
    model = LinearVoltageOpticalModel(
        n_eff0=2.4,
        dn_eff_dv=-1e-4,
        loss_db_per_cm0=2.0,
        dloss_db_per_cm_dv=0.5,
        reference_voltage=0.5,
    )

    state = model.state_for_voltage(1.5, length_um=30.0)

    assert state.voltage == pytest.approx(1.5)
    assert state.n_eff == pytest.approx(2.3999)
    assert state.loss_db_per_cm == pytest.approx(2.5)
    assert 0.0 < state.alpha <= 1.0


def test_linear_voltage_model_rejects_negative_loss():
    model = LinearVoltageOpticalModel(
        n_eff0=2.4,
        dn_eff_dv=0.0,
        loss_db_per_cm0=0.0,
        dloss_db_per_cm_dv=-1.0,
    )

    with pytest.raises(ValueError):
        model.state_for_voltage(1.0, length_um=30.0)


def test_table_voltage_model_interpolates_state():
    model = TableVoltageOpticalModel(
        rows=[
            {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
            {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
        ]
    )

    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.voltage == pytest.approx(0.5)
    assert state.n_eff == pytest.approx(2.3995)
    assert state.loss_db_per_cm == pytest.approx(2.5)
    assert 0.0 < state.alpha <= 1.0


def test_table_voltage_model_interpolates_optional_values():
    model = TableVoltageOpticalModel(
        rows=[
            {
                "voltage": 0.0,
                "n_eff": 2.4,
                "loss_db_per_cm": 2.0,
                "n_group": 4.0,
                "capacitance_f": 4e-14,
            },
            {
                "voltage": 1.0,
                "n_eff": 2.399,
                "loss_db_per_cm": 3.0,
                "n_group": 4.2,
                "capacitance_f": 2e-14,
            },
        ]
    )

    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_group == pytest.approx(4.1)
    assert state.capacitance_f == pytest.approx(3e-14)


def test_table_voltage_model_can_read_csv(tmp_path):
    path = tmp_path / "table.csv"
    path.write_text(
        "voltage,n_eff,loss_db_per_cm,n_group,capacitance_f\n"
        "0.0,2.4,2.0,4.0,4e-14\n"
        "1.0,2.399,3.0,4.2,2e-14\n"
    )

    model = TableVoltageOpticalModel.from_csv(path)
    state = model.state_for_voltage(0.25, length_um=30.0)

    assert state.n_eff == pytest.approx(2.39975)
    assert state.loss_db_per_cm == pytest.approx(2.25)


def test_table_voltage_model_rejects_out_of_range_voltage():
    model = TableVoltageOpticalModel(
        rows=[
            {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
            {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
        ]
    )

    with pytest.raises(ValueError):
        model.state_for_voltage(2.0, length_um=30.0)


def test_table_voltage_model_rejects_missing_required_columns():
    with pytest.raises(ValueError):
        TableVoltageOpticalModel(
            rows=[
                {"voltage": 0.0, "n_eff": 2.4},
                {"voltage": 1.0, "n_eff": 2.399},
            ]
        )


def test_table_voltage_model_accepts_aliases_and_capacitance_units():
    model = TableVoltageOpticalModel(
        rows=[
            {"V": 0.0, "neff": 2.4, "loss_dB_per_cm": 2.0, "capacitance_ff": 40.0},
            {"V": 1.0, "neff": 2.399, "loss_dB_per_cm": 3.0, "capacitance_ff": 20.0},
        ]
    )

    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff == pytest.approx(2.3995)
    assert state.loss_db_per_cm == pytest.approx(2.5)
    assert state.capacitance_f == pytest.approx(30e-15)


def test_table_voltage_model_accepts_ne_ng_loss_aliases():
    model = TableVoltageOpticalModel(
        rows=[
            {"bias": 0.0, "ne": 2.4, "ng": 4.0, "loss": 2.0},
            {"bias": 1.0, "ne": 2.399, "ng": 4.2, "loss": 3.0},
        ]
    )

    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff == pytest.approx(2.3995)
    assert state.n_group == pytest.approx(4.1)
    assert state.loss_db_per_cm == pytest.approx(2.5)


def test_table_voltage_model_can_extrapolate_when_enabled():
    model = TableVoltageOpticalModel(
        rows=[
            {"voltage": 0.0, "n_eff": 2.4, "loss_db_per_cm": 2.0},
            {"voltage": 1.0, "n_eff": 2.399, "loss_db_per_cm": 3.0},
        ],
        allow_extrapolation=True,
    )

    state = model.state_for_voltage(2.0, length_um=30.0)

    assert state.n_eff == pytest.approx(2.398)
    assert state.loss_db_per_cm == pytest.approx(4.0)
