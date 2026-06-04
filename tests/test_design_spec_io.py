import json
from pathlib import Path

import pytest

from ringresonator_study.io import (
    load_ring_modulator_design_input,
    load_ring_modulator_design_spec,
    ring_modulator_design_input_from_dict,
)
from ringresonator_study.modulation import design_ring_modulator


def test_load_ring_modulator_design_input_uses_separated_sections(tmp_path: Path):
    path = tmp_path / "design.json"
    path.write_text(
        json.dumps(
            {
                "resonator": {
                    "type": "single_add_drop",
                    "candidates": [
                        {
                            "input_t": 0.88,
                            "output_t": 0.90,
                            "length_um": 30.0,
                            "intrinsic_alpha": 0.98,
                        },
                        {
                            "input_t": 0.92,
                            "length_um": 32.0,
                        },
                    ],
                },
                "modulation": {
                    "mechanism": "carrier_extraction",
                    "voltage_model": {
                        "type": "table",
                        "rows": [
                            {
                                "voltage": 0.0,
                                "n_eff": 2.395,
                                "n_group": 4.16,
                                "loss_db_per_cm": 6.0,
                                "capacitance_f": 45e-15,
                            },
                            {
                                "voltage": 1.0,
                                "n_eff": 2.399,
                                "n_group": 4.20,
                                "loss_db_per_cm": 3.2,
                                "capacitance_f": 32e-15,
                            },
                        ],
                    },
                },
                "sweep": {
                    "wavelengths_um": {"start": 1.54, "stop": 1.56, "count": 3},
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                    "port": "through",
                    "resistance_ohm": 50.0,
                },
                "constraints": {
                    "max_insertion_loss_db": 20.0,
                    "min_extinction_ratio_db": 0.0,
                },
                "scoring": {"bandwidth_weight": 1.0},
                "execution": {"skip_invalid": True},
            }
        )
    )

    design_input = load_ring_modulator_design_input(path)

    assert len(list(design_input.spec.candidates)) == 2
    assert list(design_input.spec.wavelengths_um) == pytest.approx([1.54, 1.55, 1.56])
    assert list(design_input.spec.bias_voltages) == [0.5]
    results = design_ring_modulator(design_input.voltage_model, design_input.spec)
    assert results


def test_load_ring_modulator_design_input_resolves_relative_csv(tmp_path: Path):
    csv_path = tmp_path / "voltage.csv"
    csv_path.write_text(
        "voltage,ne,ng,loss,capacitance_ff\n"
        "0.0,2.395,4.16,6.0,45.0\n"
        "1.0,2.399,4.20,3.2,32.0\n"
    )
    json_path = tmp_path / "design.json"
    json_path.write_text(
        json.dumps(
            {
                "resonator": {
                    "candidates": [{"input_t": 0.9, "length_um": 30.0}]
                },
                "modulation": {
                    "voltage_model": {
                        "type": "csv",
                        "path": "voltage.csv",
                    }
                },
                "sweep": {
                    "wavelengths_um": [1.55],
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                },
            }
        )
    )

    design_input = load_ring_modulator_design_input(json_path)
    state = design_input.voltage_model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff == pytest.approx(2.397)
    assert state.n_group == pytest.approx(4.18)
    assert state.loss_db_per_cm == pytest.approx(4.6)
    assert state.capacitance_f == pytest.approx(38.5e-15)


def test_load_ring_modulator_design_input_can_use_provisional_modulation():
    design_input = ring_modulator_design_input_from_dict(
        {
            "resonator": {"candidates": [{"input_t": 0.9, "length_um": 30.0}]},
            "modulation": {"mechanism": "carrier_extraction"},
            "sweep": {
                "wavelengths_um": [1.55],
                "bias_voltages": [0.5],
                "drive_voltage": 0.4,
            },
        }
    )

    state = design_input.voltage_model.state_for_voltage(0.5, length_um=30.0)

    assert state.n_eff > 0
    assert state.loss_db_per_cm is not None


def test_load_ring_modulator_design_spec_returns_spec_only(tmp_path: Path):
    path = tmp_path / "design.json"
    path.write_text(
        json.dumps(
            {
                "resonator": {"candidates": [{"input_t": 0.9, "length_um": 30.0}]},
                "sweep": {
                    "wavelengths_um": [1.55],
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                },
            }
        )
    )

    spec = load_ring_modulator_design_spec(path)

    assert list(spec.bias_voltages) == [0.5]


def test_ring_modulator_design_input_rejects_unknown_keys():
    with pytest.raises(ValueError, match="unknown design input keys"):
        ring_modulator_design_input_from_dict(
            {
                "resonator": {"candidates": [{"input_t": 0.9, "length_um": 30.0}]},
                "sweep": {
                    "wavelengths_um": [1.55],
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                },
                "unexpected": True,
            }
        )


def test_ring_modulator_design_input_rejects_invalid_range():
    with pytest.raises(ValueError, match="wavelengths_um count must be positive"):
        ring_modulator_design_input_from_dict(
            {
                "resonator": {"candidates": [{"input_t": 0.9, "length_um": 30.0}]},
                "sweep": {
                    "wavelengths_um": {"start": 1.55, "stop": 1.56, "count": 0},
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                },
            }
        )


def test_ring_modulator_design_input_rejects_unknown_resonator_type():
    with pytest.raises(ValueError, match="resonator type"):
        ring_modulator_design_input_from_dict(
            {
                "resonator": {
                    "type": "vernier",
                    "candidates": [{"input_t": 0.9, "length_um": 30.0}],
                },
                "sweep": {
                    "wavelengths_um": [1.55],
                    "bias_voltages": [0.5],
                    "drive_voltage": 0.4,
                },
            }
        )
