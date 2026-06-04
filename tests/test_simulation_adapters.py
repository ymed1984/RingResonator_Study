import pytest

from ringresonator_study.io import (
    load_lumerical_fde_voltage_model,
    load_sentaurus_voltage_model,
    read_sentaurus_capacitance_rows,
    read_sentaurus_voltage_rows,
)


def test_load_lumerical_fde_voltage_model_accepts_aliases(tmp_path):
    path = tmp_path / "fde.csv"
    path.write_text(
        "V,ne,loss,ng\n"
        "0.0,2.4,2.0,4.0\n"
        "1.0,2.399,3.0,4.2\n"
    )

    model = load_lumerical_fde_voltage_model(path)
    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff == pytest.approx(2.3995)
    assert state.n_group == pytest.approx(4.1)
    assert state.loss_db_per_cm == pytest.approx(2.5)


def test_load_lumerical_fde_voltage_model_can_use_provisional_data():
    model = load_lumerical_fde_voltage_model()
    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff > 0
    assert state.n_group is not None
    assert state.loss_db_per_cm is not None


def test_load_sentaurus_voltage_model_accepts_optical_aliases(tmp_path):
    path = tmp_path / "sentaurus_optical.csv"
    path.write_text(
        "bias,ne,ng,loss,capacitance_ff\n"
        "0.0,2.4,4.0,2.0,40.0\n"
        "1.0,2.399,4.2,3.0,20.0\n"
    )

    rows = read_sentaurus_voltage_rows(path)
    model = load_sentaurus_voltage_model(path)
    state = model.state_for_voltage(0.5, length_um=30.0)

    assert rows[0]["n_eff"] == pytest.approx(2.4)
    assert rows[0]["loss_db_per_cm"] == pytest.approx(2.0)
    assert rows[0]["capacitance_f"] == pytest.approx(40e-15)
    assert state.n_eff == pytest.approx(2.3995)
    assert state.n_group == pytest.approx(4.1)
    assert state.loss_db_per_cm == pytest.approx(2.5)
    assert state.capacitance_f == pytest.approx(30e-15)


def test_load_sentaurus_voltage_model_can_use_provisional_data():
    model = load_sentaurus_voltage_model()
    state = model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff > 0
    assert state.n_group is not None
    assert state.loss_db_per_cm is not None


def test_read_sentaurus_capacitance_rows_accepts_common_aliases(tmp_path):
    path = tmp_path / "device.csv"
    path.write_text(
        "bias_voltage,capacitance_ff,junction_current\n"
        "0.0,40.0,1e-9\n"
        "1.0,20.0,2e-9\n"
    )

    rows = read_sentaurus_capacitance_rows(path)

    assert rows == [
        {
            "voltage": pytest.approx(0.0),
            "capacitance_f": pytest.approx(40e-15),
            "junction_current_a": pytest.approx(1e-9),
        },
        {
            "voltage": pytest.approx(1.0),
            "capacitance_f": pytest.approx(20e-15),
            "junction_current_a": pytest.approx(2e-9),
        },
    ]
