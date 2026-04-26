"""Phase helpers for ring resonator models."""

from __future__ import annotations

import math


def round_trip_phase(wavelength: float, *, n_eff: float, length: float) -> float:
    """Compute ring round-trip phase ``phi = beta L``.

    ``wavelength`` and ``length`` must use the same unit.
    """

    if wavelength <= 0:
        raise ValueError("wavelength must be positive")
    return 2 * math.pi * n_eff * length / wavelength
