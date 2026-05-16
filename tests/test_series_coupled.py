import math

import pytest

from ringresonator_study import SeriesCoupledRings
from ringresonator_study.models.series_coupled import radius_for_fsr


def test_ansys_nominal_constructor_sets_design_values():
    model = SeriesCoupledRings.ansys_nominal_two_ring()

    assert model.ring_count == 2
    assert model.kappa1_power == pytest.approx(0.13)
    assert model.kappa2_power == pytest.approx(0.0047)
    assert model.design.fsr_ghz == pytest.approx(79.5)
    assert model.design.radius_um == pytest.approx(154, abs=1)


def test_crow_response_exposes_power_and_phase():
    model = SeriesCoupledRings.ansys_nominal_two_ring()

    response = model.response_for_wavelength(1.55)

    assert response.drop.power >= 0.0
    assert response.through.power >= 0.0
    assert -math.pi <= response.drop.phase <= math.pi


def test_supports_more_than_two_rings():
    model = SeriesCoupledRings.from_fsr(
        ring_count=4,
        fsr_hz=79.5e9,
        kappa1_power=0.13,
        kappa2_power=0.0047,
        n_eff=2.566,
        n_group=3.893,
    )

    response = model.response_for_wavelength(1.55)

    assert model.ring_count == 4
    assert response.drop.power >= 0.0


def test_rejects_invalid_tuning_vector_length():
    with pytest.raises(ValueError):
        SeriesCoupledRings(
            ring_count=2,
            kappa1_power=0.13,
            kappa2_power=0.0047,
            radius_um=154,
            n_eff=2.566,
            n_group=3.893,
            tuning_voltages=(0.0, 0.1, 0.2),
        )


def test_radius_for_fsr_matches_ansys_example():
    radius_um = radius_for_fsr(fsr_hz=79.5e9, n_group=3.893)

    assert radius_um == pytest.approx(154, abs=1)
