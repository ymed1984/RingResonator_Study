import math
import unittest

from ringresonator_study import SeriesCoupledRings
from ringresonator_study.models.series_coupled import radius_for_fsr


class SeriesCoupledRingsTest(unittest.TestCase):
    def test_ansys_nominal_constructor_sets_design_values(self):
        model = SeriesCoupledRings.ansys_nominal_two_ring()

        self.assertEqual(model.ring_count, 2)
        self.assertAlmostEqual(model.kappa1_power, 0.13)
        self.assertAlmostEqual(model.kappa2_power, 0.0047)
        self.assertAlmostEqual(model.design.fsr_ghz, 79.5)
        self.assertAlmostEqual(model.design.radius_um, 154, delta=1)

    def test_crow_response_exposes_power_and_phase(self):
        model = SeriesCoupledRings.ansys_nominal_two_ring()

        response = model.response_for_wavelength(1.55)

        self.assertGreaterEqual(response.drop.power, 0.0)
        self.assertGreaterEqual(response.through.power, 0.0)
        self.assertTrue(-math.pi <= response.drop.phase <= math.pi)

    def test_supports_more_than_two_rings(self):
        model = SeriesCoupledRings.from_fsr(
            ring_count=4,
            fsr_hz=79.5e9,
            kappa1_power=0.13,
            kappa2_power=0.0047,
            n_eff=2.566,
            n_group=3.893,
        )

        response = model.response_for_wavelength(1.55)

        self.assertEqual(model.ring_count, 4)
        self.assertGreaterEqual(response.drop.power, 0.0)

    def test_rejects_invalid_tuning_vector_length(self):
        with self.assertRaises(ValueError):
            SeriesCoupledRings(
                ring_count=2,
                kappa1_power=0.13,
                kappa2_power=0.0047,
                radius_um=154,
                n_eff=2.566,
                n_group=3.893,
                tuning_voltages=(0.0, 0.1, 0.2),
            )

    def test_radius_for_fsr_matches_ansys_example(self):
        radius_um = radius_for_fsr(fsr_hz=79.5e9, n_group=3.893)

        self.assertAlmostEqual(radius_um, 154, delta=1)


if __name__ == "__main__":
    unittest.main()
