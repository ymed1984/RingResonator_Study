"""Reusable photonic components."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Coupler:
    """Directional coupler field coefficients.

    Args:
        t: Through/self-coupling field coefficient.
        kappa: Cross-coupling field coefficient.

    For an ideal lossless coupler, ``abs(t)**2 + abs(kappa)**2 == 1``.
    """

    t: complex
    kappa: complex

    @classmethod
    def lossless_from_t(cls, t: complex, *, kappa_phase: complex = 1j) -> "Coupler":
        """Build a lossless coupler from its through field coefficient.

        ``kappa_phase`` controls the phase convention for the cross-coupling term.
        The default ``1j`` matches the examples in this project.
        """

        cross_power = 1 - abs(t) ** 2
        if cross_power < 0:
            raise ValueError("lossless coupler requires abs(t) <= 1")
        if abs(kappa_phase) == 0:
            raise ValueError("kappa_phase must be non-zero")

        phase = kappa_phase / abs(kappa_phase)
        return cls(t=t, kappa=phase * math.sqrt(cross_power))

    @property
    def through_power(self) -> float:
        return abs(self.t) ** 2

    @property
    def cross_power(self) -> float:
        return abs(self.kappa) ** 2

    def validate_lossless(self, *, tolerance: float = 1e-12) -> None:
        total = self.through_power + self.cross_power
        if not math.isclose(total, 1.0, rel_tol=tolerance, abs_tol=tolerance):
            raise ValueError(
                "lossless coupler requires abs(t)**2 + abs(kappa)**2 == 1; "
                f"got {total:.16g}"
            )
