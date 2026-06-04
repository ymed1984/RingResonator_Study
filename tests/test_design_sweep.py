import pytest

from ringresonator_study.modulation import (
    LinearVoltageOpticalModel,
    RingDesignCandidate,
    RingModulatorDesignCandidate,
    RingModulatorDesignSpec,
    TableVoltageOpticalModel,
    design_ring_modulator,
    sweep_ring_designs,
)


def test_sweep_ring_designs_returns_ranked_results():
    voltage_model = LinearVoltageOpticalModel(
        n_eff0=2.4,
        dn_eff_dv=-1e-3,
        loss_db_per_cm0=2.0,
        dloss_db_per_cm_dv=0.5,
    )

    results = sweep_ring_designs(
        voltage_model,
        [
            RingDesignCandidate(through_t=0.9, length_um=30.0),
            RingDesignCandidate(through_t=0.95, length_um=30.0),
        ],
        wavelengths_um=[1.54, 1.55],
        bias_voltages=[0.5, 1.0],
        drive_voltage=0.4,
    )

    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert "best_wavelength" in results[0].as_dict()


def test_sweep_ring_designs_rejects_invalid_candidate():
    voltage_model = LinearVoltageOpticalModel(n_eff0=2.4, dn_eff_dv=-1e-3)

    with pytest.raises(ValueError):
        sweep_ring_designs(
            voltage_model,
            [RingDesignCandidate(through_t=0.9, length_um=0.0)],
            wavelengths_um=[1.55],
            bias_voltages=[0.5],
            drive_voltage=0.4,
        )


def build_table_voltage_model(*, capacitance: bool = True) -> TableVoltageOpticalModel:
    rows = [
        {
            "voltage": 0.0,
            "n_eff": 2.4,
            "loss_db_per_cm": 2.0,
        },
        {
            "voltage": 1.0,
            "n_eff": 2.399,
            "loss_db_per_cm": 3.0,
        },
    ]
    if capacitance:
        rows[0]["capacitance_f"] = 40e-15
        rows[1]["capacitance_f"] = 20e-15
    return TableVoltageOpticalModel(rows)


def build_design_spec(**overrides) -> RingModulatorDesignSpec:
    settings = {
        "candidates": [
            RingModulatorDesignCandidate(input_t=0.9, length_um=30.0),
            RingModulatorDesignCandidate(input_t=0.95, length_um=30.0),
        ],
        "wavelengths_um": [1.54, 1.55],
        "bias_voltages": [0.5],
        "drive_voltage": 0.4,
    }
    settings.update(overrides)
    return RingModulatorDesignSpec(**settings)


def test_design_ring_modulator_returns_ranked_results():
    results = design_ring_modulator(build_table_voltage_model(), build_design_spec())

    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert results[0].constraints_passed is True
    assert "rc_bandwidth_ghz" in results[0].as_dict()


def test_design_ring_modulator_filters_by_optical_constraints():
    unconstrained = design_ring_modulator(build_table_voltage_model(), build_design_spec())
    best_extinction_ratio = max(result.best.extinction_ratio_db for result in unconstrained)

    results = design_ring_modulator(
        build_table_voltage_model(),
        build_design_spec(min_extinction_ratio_db=best_extinction_ratio),
    )

    assert results
    assert all(
        result.best.extinction_ratio_db >= best_extinction_ratio for result in results
    )


def test_design_ring_modulator_calculates_rc_bandwidth_from_table_capacitance():
    results = design_ring_modulator(
        build_table_voltage_model(capacitance=True),
        build_design_spec(resistance_ohm=50.0),
    )

    assert results[0].rc_bandwidth_ghz is not None
    assert results[0].rc_bandwidth_ghz > 0


def test_design_ring_modulator_omits_rc_bandwidth_without_capacitance():
    results = design_ring_modulator(
        build_table_voltage_model(capacitance=False),
        build_design_spec(),
    )

    assert results[0].rc_bandwidth_ghz is None
    assert results[0].score == pytest.approx(
        results[0].best.extinction_ratio_db - results[0].best.insertion_loss_db
    )


def test_design_ring_modulator_uses_symmetric_output_t_by_default():
    results = design_ring_modulator(
        build_table_voltage_model(),
        build_design_spec(
            candidates=[RingModulatorDesignCandidate(input_t=0.92, length_um=30.0)]
        ),
    )

    assert results[0].candidate.effective_output_t == pytest.approx(0.92)
    assert results[0].as_dict()["output_t"] == pytest.approx(0.92)


def test_design_ring_modulator_can_use_asymmetric_couplers():
    results = design_ring_modulator(
        build_table_voltage_model(),
        build_design_spec(
            candidates=[
                RingModulatorDesignCandidate(
                    input_t=0.92,
                    output_t=0.97,
                    length_um=30.0,
                )
            ]
        ),
    )

    assert results[0].candidate.effective_output_t == pytest.approx(0.97)
    assert results[0].as_dict()["output_t"] == pytest.approx(0.97)


def test_design_ring_modulator_rejects_invalid_inputs():
    voltage_model = build_table_voltage_model()

    with pytest.raises(ValueError):
        design_ring_modulator(
            voltage_model,
            build_design_spec(
                candidates=[
                    RingModulatorDesignCandidate(input_t=0.9, length_um=0.0)
                ]
            ),
        )

    with pytest.raises(ValueError):
        design_ring_modulator(voltage_model, build_design_spec(port="monitor"))

    with pytest.raises(ValueError):
        design_ring_modulator(voltage_model, build_design_spec(candidates=[]))


def test_design_ring_modulator_rejects_when_all_candidates_fail():
    with pytest.raises(ValueError):
        design_ring_modulator(
            build_table_voltage_model(),
            build_design_spec(min_extinction_ratio_db=1e9),
        )


def test_design_ring_modulator_filters_by_rc_bandwidth_constraint():
    unconstrained = design_ring_modulator(
        build_table_voltage_model(capacitance=True),
        build_design_spec(),
    )
    best_bandwidth = max(result.rc_bandwidth_ghz for result in unconstrained)

    results = design_ring_modulator(
        build_table_voltage_model(capacitance=True),
        build_design_spec(min_rc_bandwidth_ghz=best_bandwidth),
    )

    assert results
    assert all(result.rc_bandwidth_ghz >= best_bandwidth for result in results)
