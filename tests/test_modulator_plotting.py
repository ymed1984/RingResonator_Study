from pathlib import Path

import pytest

from ringresonator_study.plotting import (
    plot_bias_spectra,
    plot_operating_point_heatmap,
    plot_transfer_curve,
)


def test_plot_bias_spectra_writes_output(tmp_path: Path):
    rows = [
        {
            "wavelength": 1.54,
            "voltage": 0.0,
            "through_power": 0.9,
            "through_transmission_db": -0.45,
            "through_phase": 0.0,
        },
        {
            "wavelength": 1.55,
            "voltage": 0.0,
            "through_power": 0.7,
            "through_transmission_db": -1.55,
            "through_phase": 0.1,
        },
        {
            "wavelength": 1.54,
            "voltage": 1.0,
            "through_power": 0.8,
            "through_transmission_db": -0.97,
            "through_phase": 0.0,
        },
        {
            "wavelength": 1.55,
            "voltage": 1.0,
            "through_power": 0.95,
            "through_transmission_db": -0.22,
            "through_phase": 0.1,
        },
    ]

    output_path = plot_bias_spectra(
        rows,
        port="through",
        y_axis="db",
        output_path=tmp_path / "bias.png",
    )

    assert output_path.exists()


def test_plot_bias_spectra_rejects_unknown_axis(tmp_path: Path):
    with pytest.raises(ValueError):
        plot_bias_spectra([], y_axis="unknown", output_path=tmp_path / "bias.png")


def test_plot_transfer_curve_writes_output(tmp_path: Path):
    rows = [
        {
            "voltage": 1.0,
            "through_power": 0.9,
            "through_transmission_db": -0.45,
            "through_phase": 0.0,
        },
        {
            "voltage": 0.0,
            "through_power": 0.7,
            "through_transmission_db": -1.55,
            "through_phase": 0.1,
        },
    ]

    output_path = plot_transfer_curve(
        rows,
        port="through",
        y_axis="db",
        output_path=tmp_path / "transfer.png",
    )

    assert output_path.exists()


def test_plot_transfer_curve_rejects_unknown_port(tmp_path: Path):
    with pytest.raises(ValueError):
        plot_transfer_curve([], port="monitor", output_path=tmp_path / "transfer.png")


def test_plot_operating_point_heatmap_writes_output(tmp_path: Path):
    points = [
        {"wavelength": 1.54, "bias_voltage": 0.0, "score": 1.0},
        {"wavelength": 1.55, "bias_voltage": 0.0, "score": 2.0},
        {"wavelength": 1.54, "bias_voltage": 1.0, "score": 3.0},
        {"wavelength": 1.55, "bias_voltage": 1.0, "score": 4.0},
    ]

    output_path = plot_operating_point_heatmap(
        points,
        metric="score",
        output_path=tmp_path / "heatmap.png",
    )

    assert output_path.exists()


def test_plot_operating_point_heatmap_rejects_unknown_metric(tmp_path: Path):
    with pytest.raises(ValueError):
        plot_operating_point_heatmap(
            [{"wavelength": 1.55, "bias_voltage": 0.0, "score": 1.0}],
            metric="unknown",
            output_path=tmp_path / "heatmap.png",
        )
