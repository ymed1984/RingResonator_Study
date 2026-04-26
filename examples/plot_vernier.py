from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import VernierRing  # noqa: E402
from ringresonator_study.plotting import plot_vernier_phase, plot_vernier_power  # noqa: E402


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    vernier = VernierRing.from_design(
        center_wavelength=1.55,
        ring1_fsr=0.001,
        target_vernier_factor=25.0,
        n_eff_ring1=2.4,
        n_eff_ring2=2.4,
        n_group=4.5,
        alpha=0.98,
    )
    rows = vernier.spectrum(linspace(1.50, 1.60, 4001))
    power_path = plot_vernier_power(
        rows,
        output_path=Path("output/vernier_response.png"),
    )
    phase_path = plot_vernier_phase(
        rows,
        output_path=Path("output/vernier_phase.png"),
    )
    print(power_path)
    print(phase_path)


if __name__ == "__main__":
    main()
