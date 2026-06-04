"""Voltage-dependent modulation models and metrics."""

from .design_sweep import (
    DesignSweepResult,
    RingDesignCandidate,
    RingModulatorDesignCandidate,
    RingModulatorDesignResult,
    RingModulatorDesignSpec,
    design_ring_modulator,
    sweep_ring_designs,
)
from .electrical import (
    RCElectricalState,
    rc_3db_bandwidth_hz,
    rc_lowpass_magnitude,
    rc_state_for_voltage,
    rc_time_constant_s,
)
from .metrics import ModulationMetrics, calculate_modulation_metrics
from .operating_point import (
    OperatingPoint,
    analyze_operating_points,
    find_best_operating_point,
    rank_operating_points,
)
from .resonance import (
    ResonancePoint,
    extract_resonance_metrics,
    resonance_shifts,
    track_resonance,
)
from .voltage_models import (
    LinearVoltageOpticalModel,
    TableVoltageOpticalModel,
    VoltageOpticalModel,
    VoltageOpticalState,
    field_alpha_from_loss_db_per_cm,
    provisional_voltage_model,
    provisional_voltage_rows,
)

__all__ = [
    "LinearVoltageOpticalModel",
    "ModulationMetrics",
    "OperatingPoint",
    "DesignSweepResult",
    "RCElectricalState",
    "ResonancePoint",
    "RingDesignCandidate",
    "RingModulatorDesignCandidate",
    "RingModulatorDesignResult",
    "RingModulatorDesignSpec",
    "TableVoltageOpticalModel",
    "VoltageOpticalModel",
    "VoltageOpticalState",
    "analyze_operating_points",
    "calculate_modulation_metrics",
    "design_ring_modulator",
    "extract_resonance_metrics",
    "field_alpha_from_loss_db_per_cm",
    "find_best_operating_point",
    "rank_operating_points",
    "provisional_voltage_model",
    "provisional_voltage_rows",
    "rc_3db_bandwidth_hz",
    "rc_lowpass_magnitude",
    "rc_state_for_voltage",
    "rc_time_constant_s",
    "resonance_shifts",
    "sweep_ring_designs",
    "track_resonance",
]
