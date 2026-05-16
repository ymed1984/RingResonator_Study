from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import AddDropRing, Coupler, RingModulator  # noqa: E402
from ringresonator_study.modulation import LinearVoltageOpticalModel  # noqa: E402
from ringresonator_study.plotting import plot_bias_spectra  # noqa: E402


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
        voltage_model=LinearVoltageOpticalModel(
            n_eff0=2.4,
            dn_eff_dv=-1e-4,
            loss_db_per_cm0=2.0,
            dloss_db_per_cm_dv=0.5,
        ),
    )

    rows = modulator.bias_spectrum(
        linspace(1.50, 1.60, 2001),
        voltages=[0.0, 0.5, 1.0, 1.5],
    )
    output_path = plot_bias_spectra(
        rows,
        port="through",
        y_axis="db",
        output_path=Path("output/ring_modulator_bias_spectrum.png"),
    )
    print(output_path)


if __name__ == "__main__":
    main()
