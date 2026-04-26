"""Simple add-drop ring resonator model.

The coupler coefficients in this module are field-amplitude coefficients.
Power values are computed from complex field amplitudes as ``abs(E) ** 2``.
"""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Iterable

from ringresonator_study.components import Coupler
from ringresonator_study.phase import round_trip_phase
from ringresonator_study.responses import AddDropResponse, PortResponse


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
        denominator = self._denominator(phase)
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

    def response(self, phi: float) -> AddDropResponse:
        """Return through/drop responses at round-trip phase ``phi``."""

        through, drop = self.amplitudes(phi)
        return AddDropResponse(
            through=PortResponse(through),
            drop=PortResponse(drop),
        )

    def response_for_wavelength(
        self,
        wavelength: float,
        *,
        n_eff: float,
        length: float,
    ) -> AddDropResponse:
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
                    "through_power": response.through.power,
                    "through_phase": response.through.phase,
                    "drop_power": response.drop.power,
                    "drop_phase": response.drop.phase,
                }
            )
        return rows

    def _denominator(self, phase: complex) -> complex:
        return (
            1
            - self.alpha
            * self.input_coupler.t.conjugate()
            * self.output_coupler.t.conjugate()
            * phase
        )
