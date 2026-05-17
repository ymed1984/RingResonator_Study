from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study.io import write_csv_rows  # noqa: E402
from ringresonator_study.modulation import (  # noqa: E402
    LinearVoltageOpticalModel,
    RingDesignCandidate,
    sweep_ring_designs,
)


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    voltage_model = LinearVoltageOpticalModel(
        n_eff0=2.4,
        dn_eff_dv=-1e-3,
        loss_db_per_cm0=2.0,
        dloss_db_per_cm_dv=0.5,
    )
    candidates = [
        RingDesignCandidate(through_t=t, length_um=length_um)
        for t in [0.90, 0.93, 0.95]
        for length_um in [28.0, 30.0, 32.0]
    ]
    results = sweep_ring_designs(
        voltage_model,
        candidates,
        wavelengths_um=linspace(1.50, 1.60, 121),
        bias_voltages=linspace(0.25, 1.75, 61),
        drive_voltage=0.5,
        port="through",
    )
    output_path = write_csv_rows(
        [result.as_dict() for result in results],
        Path("output/ring_modulator_design_sweep.csv"),
    )
    print(output_path)


if __name__ == "__main__":
    main()
