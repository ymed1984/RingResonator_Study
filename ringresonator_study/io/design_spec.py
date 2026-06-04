"""JSON design-input helpers for ring modulator studies."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ringresonator_study.io.lumerical import load_lumerical_fde_voltage_model
from ringresonator_study.io.sentaurus import load_sentaurus_voltage_model
from ringresonator_study.modulation.design_sweep import (
    RingModulatorDesignCandidate,
    RingModulatorDesignSpec,
)
from ringresonator_study.modulation.voltage_models import (
    LinearVoltageOpticalModel,
    TableVoltageOpticalModel,
    VoltageOpticalModel,
    provisional_voltage_model,
)


@dataclass(frozen=True)
class RingModulatorDesignInput:
    """Separated resonator and modulation inputs for one design run."""

    voltage_model: VoltageOpticalModel
    spec: RingModulatorDesignSpec


def load_ring_modulator_design_input(path: str | Path) -> RingModulatorDesignInput:
    """Load a separated resonator/modulation design input from JSON."""

    path = Path(path)
    with path.open() as json_file:
        data = json.load(json_file)
    return ring_modulator_design_input_from_dict(data, base_path=path.parent)


def load_ring_modulator_design_spec(path: str | Path) -> RingModulatorDesignSpec:
    """Load only the design spec from a separated JSON design input."""

    return load_ring_modulator_design_input(path).spec


def ring_modulator_design_input_from_dict(
    data: dict[str, Any],
    *,
    base_path: str | Path | None = None,
) -> RingModulatorDesignInput:
    """Build design input objects from a dictionary."""

    _reject_unknown_keys(
        data,
        {"resonator", "modulation", "sweep", "constraints", "scoring", "execution"},
        "design input",
    )
    base_path = Path(base_path) if base_path is not None else Path(".")
    resonator = _required_mapping(data, "resonator")
    modulation = _optional_mapping(data, "modulation")
    sweep = _required_mapping(data, "sweep")
    constraints = _optional_mapping(data, "constraints")
    scoring = _optional_mapping(data, "scoring")
    execution = _optional_mapping(data, "execution")

    candidates = _resonator_candidates(resonator)
    voltage_model = _voltage_model_from_modulation(modulation, base_path=base_path)

    _reject_unknown_keys(
        sweep,
        {"wavelengths_um", "bias_voltages", "drive_voltage", "port", "resistance_ohm"},
        "sweep",
    )
    _reject_unknown_keys(
        constraints,
        {
            "max_insertion_loss_db",
            "min_extinction_ratio_db",
            "min_rc_bandwidth_ghz",
        },
        "constraints",
    )
    _reject_unknown_keys(
        scoring,
        {"bandwidth_weight", "bandwidth_floor_ghz"},
        "scoring",
    )
    _reject_unknown_keys(execution, {"skip_invalid"}, "execution")

    spec = RingModulatorDesignSpec(
        candidates=candidates,
        wavelengths_um=_numeric_sequence(sweep["wavelengths_um"], "wavelengths_um"),
        bias_voltages=_numeric_sequence(sweep["bias_voltages"], "bias_voltages"),
        drive_voltage=_required_float(sweep, "drive_voltage"),
        port=str(sweep.get("port", "through")),
        max_insertion_loss_db=_optional_float(
            constraints,
            "max_insertion_loss_db",
        ),
        min_extinction_ratio_db=_optional_float(
            constraints,
            "min_extinction_ratio_db",
        ),
        min_rc_bandwidth_ghz=_optional_float(
            constraints,
            "min_rc_bandwidth_ghz",
        ),
        resistance_ohm=_optional_float(sweep, "resistance_ohm", default=50.0),
        bandwidth_weight=_optional_float(scoring, "bandwidth_weight", default=1.0),
        bandwidth_floor_ghz=_optional_float(
            scoring,
            "bandwidth_floor_ghz",
            default=1e-12,
        ),
        skip_invalid=bool(execution.get("skip_invalid", True)),
    )
    return RingModulatorDesignInput(voltage_model=voltage_model, spec=spec)


def _resonator_candidates(
    resonator: dict[str, Any],
) -> list[RingModulatorDesignCandidate]:
    _reject_unknown_keys(resonator, {"type", "candidates"}, "resonator")
    resonator_type = resonator.get("type", "single_add_drop")
    if resonator_type != "single_add_drop":
        raise ValueError("resonator type must be 'single_add_drop'")

    raw_candidates = resonator.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ValueError("resonator candidates must be a non-empty list")

    candidates = []
    for index, raw_candidate in enumerate(raw_candidates):
        if not isinstance(raw_candidate, dict):
            raise ValueError(f"resonator candidate {index} must be an object")
        _reject_unknown_keys(
            raw_candidate,
            {"input_t", "output_t", "length_um", "intrinsic_alpha"},
            f"resonator candidate {index}",
        )
        candidates.append(
            RingModulatorDesignCandidate(
                input_t=_required_float(raw_candidate, "input_t"),
                output_t=_optional_float(raw_candidate, "output_t"),
                length_um=_required_float(raw_candidate, "length_um"),
                intrinsic_alpha=_optional_float(
                    raw_candidate,
                    "intrinsic_alpha",
                    default=1.0,
                ),
            )
        )
    return candidates


def _voltage_model_from_modulation(
    modulation: dict[str, Any],
    *,
    base_path: Path,
) -> VoltageOpticalModel:
    _reject_unknown_keys(modulation, {"mechanism", "voltage_model"}, "modulation")
    raw_model = modulation.get("voltage_model", {"type": "provisional"})
    if not isinstance(raw_model, dict):
        raise ValueError("modulation voltage_model must be an object")

    model_type = raw_model.get("type", "table")
    if model_type == "table":
        _reject_unknown_keys(
            raw_model,
            {"type", "rows", "allow_extrapolation"},
            "voltage_model",
        )
        rows = raw_model.get("rows")
        if not isinstance(rows, list):
            raise ValueError("table voltage_model rows must be a list")
        return TableVoltageOpticalModel(
            rows,
            allow_extrapolation=bool(raw_model.get("allow_extrapolation", False)),
        )
    if model_type == "csv":
        _reject_unknown_keys(
            raw_model,
            {"type", "path", "allow_extrapolation"},
            "voltage_model",
        )
        return TableVoltageOpticalModel.from_csv(
            _resolve_path(raw_model, base_path),
            allow_extrapolation=bool(raw_model.get("allow_extrapolation", False)),
        )
    if model_type == "lumerical_csv":
        _reject_unknown_keys(
            raw_model,
            {"type", "path", "allow_extrapolation"},
            "voltage_model",
        )
        return load_lumerical_fde_voltage_model(
            _resolve_optional_path(raw_model, base_path),
            allow_extrapolation=bool(raw_model.get("allow_extrapolation", False)),
        )
    if model_type == "sentaurus_csv":
        _reject_unknown_keys(
            raw_model,
            {"type", "path", "allow_extrapolation"},
            "voltage_model",
        )
        return load_sentaurus_voltage_model(
            _resolve_optional_path(raw_model, base_path),
            allow_extrapolation=bool(raw_model.get("allow_extrapolation", False)),
        )
    if model_type == "linear":
        _reject_unknown_keys(
            raw_model,
            {
                "type",
                "n_eff0",
                "dn_eff_dv",
                "loss_db_per_cm0",
                "dloss_db_per_cm_dv",
                "reference_voltage",
                "n_group",
                "capacitance_f",
            },
            "voltage_model",
        )
        return LinearVoltageOpticalModel(
            n_eff0=_required_float(raw_model, "n_eff0"),
            dn_eff_dv=_required_float(raw_model, "dn_eff_dv"),
            loss_db_per_cm0=_optional_float(
                raw_model,
                "loss_db_per_cm0",
                default=0.0,
            ),
            dloss_db_per_cm_dv=_optional_float(
                raw_model,
                "dloss_db_per_cm_dv",
                default=0.0,
            ),
            reference_voltage=_optional_float(
                raw_model,
                "reference_voltage",
                default=0.0,
            ),
            n_group=_optional_float(raw_model, "n_group"),
            capacitance_f=_optional_float(raw_model, "capacitance_f"),
        )
    if model_type == "provisional":
        _reject_unknown_keys(
            raw_model,
            {"type", "allow_extrapolation"},
            "voltage_model",
        )
        return provisional_voltage_model(
            allow_extrapolation=bool(raw_model.get("allow_extrapolation", False)),
        )
    raise ValueError(
        "voltage_model type must be 'table', 'csv', 'lumerical_csv', "
        "'sentaurus_csv', 'linear', or 'provisional'"
    )


def _numeric_sequence(value: Any, name: str) -> list[float]:
    if isinstance(value, list):
        if not value:
            raise ValueError(f"{name} must not be empty")
        return [float(item) for item in value]
    if isinstance(value, dict):
        _reject_unknown_keys(value, {"start", "stop", "count"}, name)
        start = _required_float(value, "start")
        stop = _required_float(value, "stop")
        count = int(value.get("count", 0))
        if count < 1:
            raise ValueError(f"{name} count must be positive")
        if count == 1:
            return [start]
        step = (stop - start) / (count - 1)
        return [start + index * step for index in range(count)]
    raise ValueError(f"{name} must be a list or range object")


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _optional_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_float(data: dict[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"missing required value: {key}")
    return float(data[key])


def _optional_float(
    data: dict[str, Any],
    key: str,
    *,
    default: float | None = None,
) -> float | None:
    if key not in data or data[key] is None:
        return default
    return float(data[key])


def _resolve_path(data: dict[str, Any], base_path: Path) -> Path:
    if "path" not in data:
        raise ValueError("voltage_model path is required")
    return _resolve_optional_path(data, base_path)  # type: ignore[return-value]


def _resolve_optional_path(data: dict[str, Any], base_path: Path) -> Path | None:
    path = data.get("path")
    if path is None:
        return None
    path = Path(path)
    if path.is_absolute():
        return path
    return base_path / path


def _reject_unknown_keys(
    data: dict[str, Any],
    allowed: set[str],
    context: str,
) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ValueError(f"unknown {context} keys: {', '.join(unknown)}")
