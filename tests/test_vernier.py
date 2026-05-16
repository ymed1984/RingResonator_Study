import math

import pytest

from ringresonator_study import VernierRing
from ringresonator_study.models.vernier import (
    synthesize_ring_length,
    vernier_fsr_from_ring_fsrs,
)


def test_synthesizes_two_different_ring_lengths():
    vernier = VernierRing.from_design(
        center_wavelength=1.55,
        ring1_fsr=0.001,
        target_vernier_factor=25.0,
        n_eff_ring1=2.4,
        n_eff_ring2=2.4,
        n_group=4.5,
        alpha=0.98,
    )

    assert vernier.ring1_length != vernier.ring2_length
    assert vernier.design.vernier_factor > 20.0
    assert vernier.design.vernier_fsr < 0.04
    assert vernier.design.vernier_fsr > 0.02


def test_vernier_response_is_product_of_ring_drop_amplitudes():
    vernier = VernierRing.from_design(alpha=0.98)

    response = vernier.response_for_wavelength(1.55)

    assert response.transmission.amplitude == pytest.approx(
        response.ring1.amplitude * response.ring2.amplitude,
    )
    assert response.transmission.power >= 0.0
    assert -math.pi <= response.transmission.phase <= math.pi


def test_synthesize_ring_length_matches_near_resonance_order():
    length = synthesize_ring_length(
        center_wavelength=1.55,
        n_group=4.5,
        n_eff=2.4,
        min_fsr=0.001,
    )
    order = length * 2.4 / 1.55

    assert order % 1.0 == pytest.approx(0.5)


def test_vernier_fsr_is_infinite_for_equal_fsrs():
    assert math.isinf(vernier_fsr_from_ring_fsrs(0.001, 0.001))
