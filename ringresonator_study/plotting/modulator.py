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


def plot_operating_point_heatmap(
    points: Iterable[object],
    *,
    metric: str = "score",
    output_path: str | Path,
) -> Path:
    """Plot an operating-point metric over wavelength and bias voltage."""

    metric_labels = {
        "score": "Score",
        "extinction_ratio_db": "Extinction ratio [dB]",
        "insertion_loss_db": "Insertion loss [dB]",
        "optical_modulation_amplitude": "OMA",
    }
    if metric not in metric_labels:
        raise ValueError(
            "metric must be 'score', 'extinction_ratio_db', "
            "'insertion_loss_db', or 'optical_modulation_amplitude'"
        )

    points = list(points)
    if not points:
        raise ValueError("points must not be empty")

    wavelengths = sorted({_value(point, "wavelength") for point in points})
    bias_voltages = sorted({_value(point, "bias_voltage") for point in points})
    values = [[float("nan") for _ in wavelengths] for _ in bias_voltages]
    wavelength_index = {value: index for index, value in enumerate(wavelengths)}
    bias_index = {value: index for index, value in enumerate(bias_voltages)}
    for point in points:
        row = bias_index[_value(point, "bias_voltage")]
        column = wavelength_index[_value(point, "wavelength")]
        values[row][column] = _value(point, metric)

    fig, ax = plt.subplots(figsize=(8.2, 5.2), constrained_layout=True)
    mesh = ax.pcolormesh(wavelengths, bias_voltages, values, shading="auto")
    colorbar = fig.colorbar(mesh, ax=ax)
    colorbar.set_label(metric_labels[metric])
    ax.set_xlabel("Wavelength [um]")
    ax.set_ylabel("Bias voltage [V]")
    ax.set_title(f"Operating point {metric_labels[metric].lower()}")

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


def _value(point: object, key: str) -> float:
    if isinstance(point, dict):
        return float(point[key])
    return float(getattr(point, key))
