import math
import unittest

from ringresonator_study import AddDropRing, Coupler
from ringresonator_study.add_drop import round_trip_phase


class AddDropRingTest(unittest.TestCase):
    def test_lossless_coupler_validation(self):
        Coupler(t=0.8, kappa=0.6j).validate_lossless()

        with self.assertRaises(ValueError):
            Coupler(t=0.8, kappa=0.7j).validate_lossless()

    def test_critical_coupling_suppresses_through_port_on_resonance(self):
        alpha = 0.9
        t1 = alpha * 0.95
        t2 = 0.95
        ring = AddDropRing(
            input_coupler=Coupler(t=t1, kappa=1j * math.sqrt(1 - t1**2)),
            output_coupler=Coupler(t=t2, kappa=1j * math.sqrt(1 - t2**2)),
            alpha=alpha,
        )

        response = ring.response(phi=0.0)

        self.assertAlmostEqual(response["through"].power, 0.0, places=28)
        self.assertGreater(response["drop"].power, 0.0)

    def test_symmetric_lossless_add_drop_ring_drops_all_power_on_resonance(self):
        t = 0.9
        ring = AddDropRing(
            input_coupler=Coupler(t=t, kappa=1j * math.sqrt(1 - t**2)),
            output_coupler=Coupler(t=t, kappa=1j * math.sqrt(1 - t**2)),
            alpha=1.0,
        )

        response = ring.response(phi=0.0)

        self.assertAlmostEqual(response["through"].power, 0.0, places=28)
        self.assertAlmostEqual(response["drop"].power, 1.0, places=14)

    def test_round_trip_phase_uses_consistent_units(self):
        phase = round_trip_phase(1.55, n_eff=2.4, length=10.0)

        self.assertAlmostEqual(phase, 2 * math.pi * 2.4 * 10.0 / 1.55)


if __name__ == "__main__":
    unittest.main()
