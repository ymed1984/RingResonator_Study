import math
import unittest

from ringresonator_study import Coupler, SeriesCoupledRings


class SeriesCoupledRingsTest(unittest.TestCase):
    def test_two_ring_constructor_sets_ring_count(self):
        model = SeriesCoupledRings.two_ring(
            input_coupler=Coupler.lossless_from_t(0.95),
            ring_coupler=Coupler.lossless_from_t(0.90),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha_1=0.98,
            alpha_2=0.97,
        )

        self.assertEqual(model.ring_count, 2)

    def test_two_ring_response_exposes_power_and_phase(self):
        model = SeriesCoupledRings.two_ring(
            input_coupler=Coupler.lossless_from_t(0.95),
            ring_coupler=Coupler.lossless_from_t(0.90),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha_1=0.98,
            alpha_2=0.97,
        )

        response = model.response((0.0, 0.0))

        self.assertGreaterEqual(response.drop.power, 0.0)
        self.assertGreaterEqual(response.through.power, 0.0)
        self.assertTrue(-math.pi <= response.drop.phase <= math.pi)

    def test_rejects_ring_count_other_than_two_for_now(self):
        with self.assertRaises(NotImplementedError):
            SeriesCoupledRings(
                bus_input_coupler=Coupler.lossless_from_t(0.95),
                ring_couplers=(
                    Coupler.lossless_from_t(0.90),
                    Coupler.lossless_from_t(0.90),
                ),
                bus_output_coupler=Coupler.lossless_from_t(0.95),
                alphas=(0.98, 0.98, 0.98),
            )


if __name__ == "__main__":
    unittest.main()
