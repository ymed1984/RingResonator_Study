from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import AddDropRing, Coupler, RingModulator  # noqa: E402
from ringresonator_study.modulation import TableVoltageOpticalModel  # noqa: E402
from ringresonator_study.plotting import plot_bias_spectra  # noqa: E402


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    # Demonstration table for carrier extraction under increasing reverse bias:
    # carriers are depleted, so free-carrier absorption decreases and the
    # effective index recovers upward. Values are provisional, not calibrated.
    voltage_model = TableVoltageOpticalModel(
        rows=[
            {
                "voltage": 0.0,
                "n_eff": 2.3950,
                "n_group": 4.16,
                "loss_db_per_cm": 6.0,
                "capacitance_f": 45e-15,
            },
            {
                "voltage": 0.5,
                "n_eff": 2.3970,
                "n_group": 4.18,
                "loss_db_per_cm": 4.5,
                "capacitance_f": 38e-15,
            },
            {
                "voltage": 1.0,
                "n_eff": 2.3990,
                "n_group": 4.20,
                "loss_db_per_cm": 3.2,
                "capacitance_f": 32e-15,
            },
            {
                "voltage": 1.5,
                "n_eff": 2.4010,
                "n_group": 4.22,
                "loss_db_per_cm": 2.4,
                "capacitance_f": 28e-15,
            },
        ],
    )

    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.88),
            output_coupler=Coupler.lossless_from_t(0.88),
            alpha=0.98,
        ),
        length_um=30.0,
        voltage_model=voltage_model,
    )

    rows = modulator.bias_spectrum(
        linspace(1.50, 1.60, 2001),
        voltages=[0.0, 0.5, 1.0, 1.5],
    )
    wavelength_path = plot_bias_spectra(
        rows,
        port="through",
        y_axis="db",
        x_axis="wavelength",
        output_path=Path("output/ring_modulator_bias_spectrum.png"),
    )
    frequency_path = plot_bias_spectra(
        rows,
        port="through",
        y_axis="db",
        x_axis="frequency",
        output_path=Path("output/ring_modulator_bias_spectrum_frequency.png"),
    )
    print(wavelength_path)
    print(frequency_path)


if __name__ == "__main__":
    main()
