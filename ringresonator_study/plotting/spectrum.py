"""Generic spectrum plotting helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def plot_power_phase_spectrum(
    rows: Iterable[dict[str, float]],
    *,
    power_keys: dict[str, str],
    phase_keys: dict[str, str],
    title: str,
    output_path: str | Path,
) -> Path:
    """Plot selected power and phase columns from spectrum rows."""

    rows = list(rows)
    wavelengths = [row["wavelength"] for row in rows]

    fig, (ax_power, ax_phase) = plt.subplots(
        2,
        1,
        figsize=(9, 6),
        sharex=True,
        constrained_layout=True,
    )

    for label, key in power_keys.items():
        ax_power.plot(wavelengths, [row[key] for row in rows], label=label, linewidth=1.8)
    ax_power.set_ylabel("Power transmission |E|^2")
    ax_power.set_title(title)
    ax_power.grid(True, alpha=0.3)
    ax_power.legend()

    for label, key in phase_keys.items():
        ax_phase.plot(wavelengths, [row[key] for row in rows], label=label, linewidth=1.8)
    ax_phase.set_xlabel("Wavelength [um]")
    ax_phase.set_ylabel("Phase arg(E) [rad]")
    ax_phase.grid(True, alpha=0.3)
    ax_phase.legend()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path
