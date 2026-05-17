import pytest

from ringresonator_study.modulation import (
    LinearVoltageOpticalModel,
    RingDesignCandidate,
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
