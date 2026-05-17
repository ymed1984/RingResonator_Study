"""Voltage-to-optical-state models for ring modulators."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class VoltageOpticalState:
    """Optical state of a modulator at one voltage bias.

    ``alpha`` is the round-trip field transmission used by ``AddDropRing``.
    ``length_um`` is assumed when deriving ``alpha`` from ``loss_db_per_cm``.
    """

    voltage: float
    n_eff: float
    alpha: float
    loss_db_per_cm: float | None = None
    n_group: float | None = None
    capacitance_f: float | None = None


class VoltageOpticalModel(Protocol):
    """Protocol for models that map voltage bias to optical state."""

    def state_for_voltage(
        self,
        voltage: float,
        *,
        length_um: float,
    ) -> VoltageOpticalState:
        """Return optical state for ``voltage`` and round-trip length."""


@dataclass(frozen=True)
class LinearVoltageOpticalModel:
    """Linear voltage model for initial ring-modulator studies."""

    n_eff0: float
    dn_eff_dv: float
    loss_db_per_cm0: float = 0.0
    dloss_db_per_cm_dv: float = 0.0
    reference_voltage: float = 0.0
    n_group: float | None = None
    capacitance_f: float | None = None

    def __post_init__(self) -> None:
        if self.n_eff0 <= 0:
            raise ValueError("n_eff0 must be positive")

    def state_for_voltage(
        self,
        voltage: float,
        *,
        length_um: float,
    ) -> VoltageOpticalState:
        if length_um <= 0:
            raise ValueError("length_um must be positive")

        voltage_delta = voltage - self.reference_voltage
        n_eff = self.n_eff0 + self.dn_eff_dv * voltage_delta
        if n_eff <= 0:
            raise ValueError("voltage model produced non-positive n_eff")

        loss_db_per_cm = self.loss_db_per_cm0 + self.dloss_db_per_cm_dv * voltage_delta
        alpha = field_alpha_from_loss_db_per_cm(loss_db_per_cm, length_um=length_um)
        return VoltageOpticalState(
            voltage=voltage,
            n_eff=n_eff,
            alpha=alpha,
            loss_db_per_cm=loss_db_per_cm,
            n_group=self.n_group,
            capacitance_f=self.capacitance_f,
        )


@dataclass(frozen=True)
class TableVoltageOpticalModel:
    """Voltage model backed by linearly interpolated tabular data."""

    rows: tuple[VoltageOpticalState, ...]
    allow_extrapolation: bool = False

    def __init__(
        self,
        rows: list[dict[str, float]] | tuple[dict[str, float], ...],
        *,
        allow_extrapolation: bool = False,
    ):
        states = tuple(_state_from_row(row) for row in rows)
        _validate_table_states(states)
        object.__setattr__(self, "rows", tuple(sorted(states, key=lambda row: row.voltage)))
        object.__setattr__(self, "allow_extrapolation", allow_extrapolation)

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        *,
        allow_extrapolation: bool = False,
    ) -> "TableVoltageOpticalModel":
        """Build a table model from a CSV file."""

        with Path(path).open(newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("CSV file must include a header row")
            rows = [_parse_csv_row(row) for row in reader]
        return cls(rows, allow_extrapolation=allow_extrapolation)

    def state_for_voltage(
        self,
        voltage: float,
        *,
        length_um: float,
    ) -> VoltageOpticalState:
        if length_um <= 0:
            raise ValueError("length_um must be positive")

        lower, upper = self._bounds_for_voltage(voltage)
        n_eff = _interpolate(voltage, lower.voltage, lower.n_eff, upper.voltage, upper.n_eff)
        loss_db_per_cm = _interpolate(
            voltage,
            lower.voltage,
            _require_value(lower.loss_db_per_cm, "loss_db_per_cm"),
            upper.voltage,
            _require_value(upper.loss_db_per_cm, "loss_db_per_cm"),
        )
        alpha = field_alpha_from_loss_db_per_cm(loss_db_per_cm, length_um=length_um)
        return VoltageOpticalState(
            voltage=voltage,
            n_eff=n_eff,
            alpha=alpha,
            loss_db_per_cm=loss_db_per_cm,
            n_group=_interpolate_optional(voltage, lower, upper, "n_group"),
            capacitance_f=_interpolate_optional(voltage, lower, upper, "capacitance_f"),
        )

    def _bounds_for_voltage(
        self,
        voltage: float,
    ) -> tuple[VoltageOpticalState, VoltageOpticalState]:
        if voltage < self.rows[0].voltage:
            if self.allow_extrapolation:
                return self.rows[0], self.rows[1]
            raise ValueError("voltage is outside the table range")
        if voltage > self.rows[-1].voltage:
            if self.allow_extrapolation:
                return self.rows[-2], self.rows[-1]
            raise ValueError("voltage is outside the table range")

        for state in self.rows:
            if voltage == state.voltage:
                return state, state

        for lower, upper in zip(self.rows, self.rows[1:], strict=True):
            if lower.voltage <= voltage <= upper.voltage:
                return lower, upper

        raise ValueError("voltage is outside the table range")


def field_alpha_from_loss_db_per_cm(loss_db_per_cm: float, *, length_um: float) -> float:
    """Return round-trip field transmission from propagation loss."""

    if length_um <= 0:
        raise ValueError("length_um must be positive")
    if loss_db_per_cm < 0:
        raise ValueError("loss_db_per_cm must be non-negative")

    length_cm = length_um * 1e-4
    return 10 ** (-(loss_db_per_cm * length_cm) / 20)


def _state_from_row(row: dict[str, float]) -> VoltageOpticalState:
    row = _normalize_voltage_row(row)
    required = {"voltage", "n_eff", "loss_db_per_cm"}
    missing = sorted(required - row.keys())
    if missing:
        raise ValueError(f"missing required table columns: {', '.join(missing)}")

    voltage = float(row["voltage"])
    n_eff = float(row["n_eff"])
    loss_db_per_cm = float(row["loss_db_per_cm"])
    if n_eff <= 0:
        raise ValueError("n_eff must be positive")
    if loss_db_per_cm < 0:
        raise ValueError("loss_db_per_cm must be non-negative")

    return VoltageOpticalState(
        voltage=voltage,
        n_eff=n_eff,
        alpha=1.0,
        loss_db_per_cm=loss_db_per_cm,
        n_group=_optional_float(row, "n_group"),
        capacitance_f=_optional_float(row, "capacitance_f"),
    )


def _parse_csv_row(row: dict[str, str | None]) -> dict[str, float]:
    return {
        key: float(value)
        for key, value in row.items()
        if key is not None and value not in {None, ""}
    }


def _normalize_voltage_row(row: dict[str, float]) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for key, value in row.items():
        canonical = _canonical_column_name(key)
        if canonical == "capacitance_ff":
            normalized["capacitance_f"] = float(value) * 1e-15
        elif canonical == "capacitance_pf":
            normalized["capacitance_f"] = float(value) * 1e-12
        else:
            normalized[canonical] = float(value)
    return normalized


def _canonical_column_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    aliases = {
        "v": "voltage",
        "voltage_v": "voltage",
        "bias": "voltage",
        "bias_voltage": "voltage",
        "bias_voltage_v": "voltage",
        "neff": "n_eff",
        "effective_index": "n_eff",
        "n_eff_real": "n_eff",
        "ng": "n_group",
        "n_g": "n_group",
        "group_index": "n_group",
        "loss": "loss_db_per_cm",
        "loss_db_cm": "loss_db_per_cm",
        "loss_db_per_cm": "loss_db_per_cm",
        "loss_db_per_centimeter": "loss_db_per_cm",
        "loss_db_per_cm_": "loss_db_per_cm",
        "loss_db_per_cm^-1": "loss_db_per_cm",
        "capacitance": "capacitance_f",
        "capacitance_f": "capacitance_f",
        "capacitance_farad": "capacitance_f",
        "capacitance_ff": "capacitance_ff",
        "capacitance_pf": "capacitance_pf",
    }
    return aliases.get(normalized, normalized)


def _validate_table_states(states: tuple[VoltageOpticalState, ...]) -> None:
    if len(states) < 2:
        raise ValueError("table voltage model requires at least two rows")
    voltages = [state.voltage for state in states]
    if len(set(voltages)) != len(voltages):
        raise ValueError("table voltage values must be unique")


def _optional_float(row: dict[str, float], key: str) -> float | None:
    value = row.get(key)
    if value is None:
        return None
    return float(value)


def _require_value(value: float | None, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required")
    return value


def _interpolate(
    x: float,
    lower_x: float,
    lower_y: float,
    upper_x: float,
    upper_y: float,
) -> float:
    if lower_x == upper_x:
        return lower_y
    fraction = (x - lower_x) / (upper_x - lower_x)
    return lower_y + fraction * (upper_y - lower_y)


def _interpolate_optional(
    voltage: float,
    lower: VoltageOpticalState,
    upper: VoltageOpticalState,
    field_name: str,
) -> float | None:
    lower_value = getattr(lower, field_name)
    upper_value = getattr(upper, field_name)
    if lower_value is None and upper_value is None:
        return None
    if lower_value is None or upper_value is None:
        raise ValueError(f"{field_name} must be present for both interpolation bounds")
    return _interpolate(
        voltage,
        lower.voltage,
        lower_value,
        upper.voltage,
        upper_value,
    )
