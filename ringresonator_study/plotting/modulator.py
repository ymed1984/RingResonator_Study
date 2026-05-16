"""Plot helpers for voltage-biased ring modulators."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def plot_bias_spectra(
    rows: Iterable[dict[str, float]],
    *,
    port: str = "through",
    y_axis: str = "db",
    output_path: str | Path,
) -> Path:
    """Plot wavelength spectra overlaid by voltage bias."""

    if port not in {"through", "drop"}:
        raise ValueError("port must be 'through' or 'drop'")
    y_key, y_label = _axis_config(port, y_axis)

    rows = list(rows)
    voltages = sorted({row["voltage"] for row in rows})

    fig, ax = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
    for voltage in voltages:
        voltage_rows = [row for row in rows if row["voltage"] == voltage]
        voltage_rows.sort(key=lambda row: row["wavelength"])
        ax.plot(
            [row["wavelength"] for row in voltage_rows],
            [row[y_key] for row in voltage_rows],
            label=f"{voltage:g} V",
            linewidth=1.7,
        )

    ax.set_xlabel("Wavelength [um]")
    ax.set_ylabel(y_label)
    ax.set_title("Ring modulator bias-dependent spectrum")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Bias")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def plot_transfer_curve(
    rows: Iterable[dict[str, float]],
    *,
    port: str = "through",
    y_axis: str = "db",
    output_path: str | Path,
) -> Path:
    """Plot fixed-wavelength transmission as a function of voltage bias."""

    if port not in {"through", "drop"}:
        raise ValueError("port must be 'through' or 'drop'")
    y_key, y_label = _axis_config(port, y_axis)

    rows = sorted(rows, key=lambda row: row["voltage"])

    fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    ax.plot(
        [row["voltage"] for row in rows],
        [row[y_key] for row in rows],
        marker="o",
        linewidth=1.7,
        markersize=3.5,
    )
    ax.set_xlabel("Bias voltage [V]")
    ax.set_ylabel(y_label)
    ax.set_title("Ring modulator transfer curve")
    ax.grid(True, alpha=0.3)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def _axis_config(port: str, y_axis: str) -> tuple[str, str]:
    if y_axis == "power":
        return f"{port}_power", f"{port.capitalize()} transmission |E|^2"
    if y_axis == "db":
        return f"{port}_transmission_db", f"{port.capitalize()} transmission [dB]"
    if y_axis == "phase":
        return f"{port}_phase", f"{port.capitalize()} phase [rad]"
    raise ValueError("y_axis must be 'power', 'db', or 'phase'")
