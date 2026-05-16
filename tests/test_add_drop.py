import math

import pytest

from ringresonator_study import AddDropRing, Coupler
from ringresonator_study.phase import round_trip_phase


def test_lossless_coupler_validation():
    Coupler(t=0.8, kappa=0.6j).validate_lossless()

    with pytest.raises(ValueError):
        Coupler(t=0.8, kappa=0.7j).validate_lossless()


def test_lossless_coupler_can_be_built_from_t():
    coupler = Coupler.lossless_from_t(0.8)

    assert coupler.through_power == pytest.approx(0.64)
    assert coupler.cross_power == pytest.approx(0.36)


def test_critical_coupling_suppresses_through_port_on_resonance():
    alpha = 0.9
    t1 = alpha * 0.95
    t2 = 0.95
    ring = AddDropRing(
        input_coupler=Coupler(t=t1, kappa=1j * math.sqrt(1 - t1**2)),
        output_coupler=Coupler(t=t2, kappa=1j * math.sqrt(1 - t2**2)),
        alpha=alpha,
    )

    response = ring.response(phi=0.0)

    assert response.through.power == pytest.approx(0.0, abs=1e-28)
    assert response.drop.power > 0.0


def test_symmetric_lossless_add_drop_ring_drops_all_power_on_resonance():
    t = 0.9
    ring = AddDropRing(
        input_coupler=Coupler(t=t, kappa=1j * math.sqrt(1 - t**2)),
        output_coupler=Coupler(t=t, kappa=1j * math.sqrt(1 - t**2)),
        alpha=1.0,
    )

    response = ring.response(phi=0.0)

    assert response.through.power == pytest.approx(0.0, abs=1e-28)
    assert response.drop.power == pytest.approx(1.0, abs=1e-14)


def test_round_trip_phase_uses_consistent_units():
    phase = round_trip_phase(1.55, n_eff=2.4, length=10.0)

    assert phase == pytest.approx(2 * math.pi * 2.4 * 10.0 / 1.55)
