from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import AddDropRing, Coupler  # noqa: E402
from ringresonator_study.plotting import plot_add_drop_response  # noqa: E402


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    ring = AddDropRing(
        input_coupler=Coupler.lossless_from_t(0.95),
        output_coupler=Coupler.lossless_from_t(0.95),
        alpha=0.98,
    )

    output_path = plot_add_drop_response(
        ring,
        linspace(1.50, 1.60, 1601),
        n_eff=2.4,
        length=30.0,
        output_path=Path("output/add_drop_response.png"),
    )
    print(output_path)


if __name__ == "__main__":
    main()
