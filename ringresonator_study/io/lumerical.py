"""CSV adapters for Lumerical FDE-derived voltage tables."""

from __future__ import annotations

from pathlib import Path

from ringresonator_study.modulation.voltage_models import TableVoltageOpticalModel


def load_lumerical_fde_voltage_model(
    path: str | Path,
    *,
    allow_extrapolation: bool = False,
) -> TableVoltageOpticalModel:
    """Load a Lumerical-style voltage/n_eff/loss CSV as a voltage model."""

    return TableVoltageOpticalModel.from_csv(
        path,
        allow_extrapolation=allow_extrapolation,
    )
