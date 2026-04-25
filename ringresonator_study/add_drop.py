"""Simple add-drop ring resonator model.

The coupler coefficients in this module are field-amplitude coefficients.
Power values are computed from complex field amplitudes as ``abs(E) ** 2``.
"""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Iterable


@dataclass(frozen=True)
class Coupler:
    """Directional coupler field coefficients.

    Args:
        t: Through/self-coupling field coefficient.
        kappa: Cross-coupling field coefficient.

    For an ideal lossless coupler, ``abs(t)**2 + abs(kappa)**2 == 1``.
    The model can still be used with non-ideal effective coefficients, but
    ``validate_lossless`` is useful when checking simple textbook examples.
    """

    t: complex
    kappa: complex

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


@dataclass(frozen=True)
class PortResponse:
    """Complex field response plus derived power and phase."""

    amplitude: complex

    @property
    def power(self) -> float:
        """Optical power transmission for unit input power."""

        return abs(self.amplitude) ** 2

    @property
    def phase(self) -> float:
        """Optical phase in radians, returned as the principal value."""

        return math.atan2(self.amplitude.imag, self.amplitude.real)

    @property
    def phase_degrees(self) -> float:
        return math.degrees(self.phase)


@dataclass(frozen=True)
class AddDropRing:
    """Add-drop ring resonator with two bus waveguides.

    The model follows the standard single-ring add-drop transfer functions:

    ``through = (t1 - alpha * conj(t2) * exp(j phi)) /
                (1 - alpha * conj(t1) * conj(t2) * exp(j phi))``

    ``drop = -conj(kappa1) * kappa2 * sqrt(alpha) * exp(j phi/2) /
              (1 - alpha * conj(t1) * conj(t2) * exp(j phi))``

    where ``alpha`` is the round-trip field transmission and ``phi`` is the
    round-trip phase. For passive rings, ``0 <= alpha <= 1``.
    """

    input_coupler: Coupler
    output_coupler: Coupler
    alpha: float = 1.0

    def __post_init__(self) -> None:
        if self.alpha < 0:
            raise ValueError("alpha must be non-negative")

    def amplitudes(self, phi: float) -> tuple[complex, complex]:
        """Return ``(through_amplitude, drop_amplitude)`` at phase ``phi``."""

        phase = cmath.exp(1j * phi)
        denominator = (
            1
            - self.alpha
            * self.input_coupler.t.conjugate()
            * self.output_coupler.t.conjugate()
            * phase
        )
        through = (
            self.input_coupler.t
            - self.alpha * self.output_coupler.t.conjugate() * phase
        ) / denominator
        drop = (
            -self.input_coupler.kappa.conjugate()
            * self.output_coupler.kappa
            * math.sqrt(self.alpha)
            * cmath.exp(0.5j * phi)
        ) / denominator
        return through, drop

    def response(self, phi: float) -> dict[str, PortResponse]:
        """Return through/drop responses at round-trip phase ``phi``."""

        through, drop = self.amplitudes(phi)
        return {
            "through": PortResponse(through),
            "drop": PortResponse(drop),
        }

    def response_for_wavelength(
        self,
        wavelength: float,
        *,
        n_eff: float,
        length: float,
    ) -> dict[str, PortResponse]:
        """Return response for a wavelength.

        Args:
            wavelength: Vacuum wavelength, in the same length unit as ``length``.
            n_eff: Effective index of the ring waveguide.
            length: Ring round-trip length.
        """

        return self.response(round_trip_phase(wavelength, n_eff=n_eff, length=length))

    def spectrum(
        self,
        wavelengths: Iterable[float],
        *,
        n_eff: float,
        length: float,
    ) -> list[dict[str, float]]:
        """Return a tabular spectrum with power and phase for each wavelength."""

        rows: list[dict[str, float]] = []
        for wavelength in wavelengths:
            response = self.response_for_wavelength(
                wavelength,
                n_eff=n_eff,
                length=length,
            )
            rows.append(
                {
                    "wavelength": wavelength,
                    "through_power": response["through"].power,
                    "through_phase": response["through"].phase,
                    "drop_power": response["drop"].power,
                    "drop_phase": response["drop"].phase,
                }
            )
        return rows


def round_trip_phase(wavelength: float, *, n_eff: float, length: float) -> float:
    """Compute ring round-trip phase ``phi = beta L``.

    ``wavelength`` and ``length`` must use the same unit.
    """

    if wavelength <= 0:
        raise ValueError("wavelength must be positive")
    return 2 * math.pi * n_eff * length / wavelength
