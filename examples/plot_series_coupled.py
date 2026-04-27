from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import SeriesCoupledRings  # noqa: E402
from ringresonator_study.plotting import plot_power_phase_spectrum  # noqa: E402


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    model = SeriesCoupledRings.ansys_nominal_two_ring(tuning_voltage=0.95)
    rows = model.spectrum(linspace(1.50, 1.60, 3001))
    output_path = plot_power_phase_spectrum(
        rows,
        power_keys={
            "through port": "through_power",
            "drop port": "drop_power",
        },
        phase_keys={
            "through port": "through_phase",
            "drop port": "drop_phase",
        },
        title="Two-stage series-coupled ring response",
        output_path=Path("output/series_coupled_response.png"),
    )
    print(output_path)


if __name__ == "__main__":
    main()
