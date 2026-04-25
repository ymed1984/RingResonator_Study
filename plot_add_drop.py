from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from ringresonator_study import AddDropRing, Coupler


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("count must be at least 2")
    step = (stop - start) / (count - 1)
    return [start + i * step for i in range(count)]


def main() -> None:
    t = 0.95
    kappa = 1j * (1 - t**2) ** 0.5
    ring = AddDropRing(
        input_coupler=Coupler(t=t, kappa=kappa),
        output_coupler=Coupler(t=t, kappa=kappa),
        alpha=0.98,
    )

    wavelengths_um = linspace(1.50, 1.60, 1601)
    rows = ring.spectrum(wavelengths_um, n_eff=2.4, length=30.0)

    through_power = [row["through_power"] for row in rows]
    drop_power = [row["drop_power"] for row in rows]
    through_phase = [row["through_phase"] for row in rows]
    drop_phase = [row["drop_phase"] for row in rows]

    fig, (ax_power, ax_phase) = plt.subplots(
        2,
        1,
        figsize=(9, 6),
        sharex=True,
        constrained_layout=True,
    )

    ax_power.plot(wavelengths_um, through_power, label="through port", linewidth=1.8)
    ax_power.plot(wavelengths_um, drop_power, label="drop port", linewidth=1.8)
    ax_power.set_ylabel("Power transmission |E|^2")
    ax_power.set_title("Add-drop ring resonator response")
    ax_power.grid(True, alpha=0.3)
    ax_power.legend()

    ax_phase.plot(wavelengths_um, through_phase, label="through port", linewidth=1.8)
    ax_phase.plot(wavelengths_um, drop_phase, label="drop port", linewidth=1.8)
    ax_phase.set_xlabel("Wavelength [um]")
    ax_phase.set_ylabel("Phase arg(E) [rad]")
    ax_phase.grid(True, alpha=0.3)
    ax_phase.legend()

    output_path = Path("output/add_drop_response.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    print(output_path)


if __name__ == "__main__":
    main()
