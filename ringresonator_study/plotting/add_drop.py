"""Plot helpers for add-drop ring resonator responses."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt

from ringresonator_study.models import AddDropRing


def plot_add_drop_response(
    ring: AddDropRing,
    wavelengths: Iterable[float],
    *,
    n_eff: float,
    length: float,
    output_path: str | Path,
) -> Path:
    """Plot through/drop power and phase over a wavelength sweep."""

    wavelengths = list(wavelengths)
    rows = ring.spectrum(wavelengths, n_eff=n_eff, length=length)

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

    ax_power.plot(wavelengths, through_power, label="through port", linewidth=1.8)
    ax_power.plot(wavelengths, drop_power, label="drop port", linewidth=1.8)
    ax_power.set_ylabel("Power transmission |E|^2")
    ax_power.set_title("Add-drop ring resonator response")
    ax_power.grid(True, alpha=0.3)
    ax_power.legend()

    ax_phase.plot(wavelengths, through_phase, label="through port", linewidth=1.8)
    ax_phase.plot(wavelengths, drop_phase, label="drop port", linewidth=1.8)
    ax_phase.set_xlabel("Wavelength [um]")
    ax_phase.set_ylabel("Phase arg(E) [rad]")
    ax_phase.grid(True, alpha=0.3)
    ax_phase.legend()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path
