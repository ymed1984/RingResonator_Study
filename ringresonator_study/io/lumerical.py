"""CSV adapters for Lumerical FDE-derived voltage tables."""

from __future__ import annotations

from pathlib import Path

from ringresonator_study.modulation.voltage_models import (
    TableVoltageOpticalModel,
    provisional_voltage_model,
)


def load_lumerical_fde_voltage_model(
    path: str | Path | None = None,
    *,
    allow_extrapolation: bool = False,
) -> TableVoltageOpticalModel:
    """Load a Lumerical-style voltage/ne/ng/loss CSV as a voltage model.

    When no direct simulator export is available yet, call without ``path`` to
    get a small provisional model with placeholder optical data.
    """

    if path is None:
        return provisional_voltage_model(allow_extrapolation=allow_extrapolation)

    return TableVoltageOpticalModel.from_csv(
        path,
        allow_extrapolation=allow_extrapolation,
    )
