from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ringresonator_study import AddDropRing, Coupler  # noqa: E402


def build_example_ring() -> AddDropRing:
    return AddDropRing(
        input_coupler=Coupler.lossless_from_t(0.95),
        output_coupler=Coupler.lossless_from_t(0.95),
        alpha=0.98,
    )


def main() -> None:
    ring = build_example_ring()
    response = ring.response(phi=0.0)
    for port, value in response.as_dict().items():
        print(
            f"{port}: amplitude={value.amplitude:.6g}, "
            f"power={value.power:.6g}, phase={value.phase:.6g} rad"
        )


if __name__ == "__main__":
    main()
