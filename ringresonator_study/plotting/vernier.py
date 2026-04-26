"""Plot helpers for Vernier ring responses."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def plot_vernier_power(
    rows: Iterable[dict[str, float]],
    *,
    output_path: str | Path,
) -> Path:
    """Plot Ring1/Ring2 powers together and Vernier power separately."""

    rows = list(rows)
    wavelengths = [row["wavelength"] for row in rows]

    fig, (ax_rings, ax_vernier) = plt.subplots(
        2,
        1,
        figsize=(9, 6),
        sharex=True,
        constrained_layout=True,
    )

    ax_rings.plot(
        wavelengths,
        [row["ring1_drop_power"] for row in rows],
        label="Ring1 drop",
        linewidth=1.6,
    )
    ax_rings.plot(
        wavelengths,
        [row["ring2_drop_power"] for row in rows],
        label="Ring2 drop",
        linewidth=1.6,
    )
    ax_rings.set_ylabel("Ring power |E|^2")
    ax_rings.set_title("Vernier ring component responses")
    ax_rings.grid(True, alpha=0.3)
    ax_rings.legend()

    ax_vernier.plot(
        wavelengths,
        [row["transmission_power"] for row in rows],
        label="Vernier transmission",
        color="black",
        linewidth=1.8,
    )
    ax_vernier.set_xlabel("Wavelength [um]")
    ax_vernier.set_ylabel("Vernier power |E|^2")
    ax_vernier.grid(True, alpha=0.3)
    ax_vernier.legend()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def plot_vernier_phase(
    rows: Iterable[dict[str, float]],
    *,
    output_path: str | Path,
) -> Path:
    """Plot Ring1/Ring2 phases together and Vernier phase separately."""

    rows = list(rows)
    wavelengths = [row["wavelength"] for row in rows]

    fig, (ax_rings, ax_vernier) = plt.subplots(
        2,
        1,
        figsize=(9, 6),
        sharex=True,
        constrained_layout=True,
    )

    ax_rings.plot(
        wavelengths,
        [row["ring1_drop_phase"] for row in rows],
        label="Ring1 drop",
        linewidth=1.6,
    )
    ax_rings.plot(
        wavelengths,
        [row["ring2_drop_phase"] for row in rows],
        label="Ring2 drop",
        linewidth=1.6,
    )
    ax_rings.set_ylabel("Ring phase [rad]")
    ax_rings.set_title("Vernier ring component phases")
    ax_rings.grid(True, alpha=0.3)
    ax_rings.legend()

    ax_vernier.plot(
        wavelengths,
        [row["transmission_phase"] for row in rows],
        label="Vernier transmission",
        color="black",
        linewidth=1.8,
    )
    ax_vernier.set_xlabel("Wavelength [um]")
    ax_vernier.set_ylabel("Vernier phase [rad]")
    ax_vernier.grid(True, alpha=0.3)
    ax_vernier.legend()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path
