from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import AddDropRing, Coupler, RingModulator  # noqa: E402
from ringresonator_study.modulation import (  # noqa: E402
    TableVoltageOpticalModel,
    track_resonance,
)
from ringresonator_study.plotting import (  # noqa: E402
    plot_bias_spectra,
    plot_transfer_curve,
)


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    modulator = RingModulator(
        ring=AddDropRing(
            input_coupler=Coupler.lossless_from_t(0.95),
            output_coupler=Coupler.lossless_from_t(0.95),
            alpha=1.0,
        ),
        length_um=30.0,
        voltage_model=TableVoltageOpticalModel(
            rows=[
                {
                    "voltage": 0.0,
                    "n_eff": 2.4000,
                    "loss_db_per_cm": 2.0,
                    "n_group": 4.2,
                    "capacitance_f": 3.5e-14,
                },
                {
                    "voltage": 0.5,
                    "n_eff": 2.3998,
                    "loss_db_per_cm": 2.2,
                    "n_group": 4.2,
                    "capacitance_f": 3.3e-14,
                },
                {
                    "voltage": 1.0,
                    "n_eff": 2.3995,
                    "loss_db_per_cm": 2.5,
                    "n_group": 4.2,
                    "capacitance_f": 3.1e-14,
                },
            ],
        ),
    )

    bias_rows = modulator.bias_spectrum(
        linspace(1.50, 1.60, 2001),
        voltages=[0.0, 0.5, 1.0],
    )
    bias_path = plot_bias_spectra(
        bias_rows,
        port="through",
        y_axis="db",
        output_path=Path("output/ring_modulator_table_bias_spectrum.png"),
    )

    resonances = track_resonance(bias_rows, port="through", mode="min")
    operating_wavelength = resonances[0]["resonance_wavelength"]
    transfer_rows = modulator.transfer_curve(
        linspace(0.0, 1.0, 41),
        wavelength_um=operating_wavelength,
    )
    transfer_path = plot_transfer_curve(
        transfer_rows,
        port="through",
        y_axis="db",
        output_path=Path("output/ring_modulator_transfer.png"),
    )

    print(bias_path)
    print(transfer_path)


if __name__ == "__main__":
    main()
