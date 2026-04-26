"""Vernier filter made from two cascaded add-drop rings."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Iterable

from ringresonator_study.components import Coupler
from ringresonator_study.models.add_drop import AddDropRing
from ringresonator_study.responses import PortResponse


@dataclass(frozen=True)
class VernierDesign:
    """Functional and physical dimensions for a two-ring Vernier filter."""

    ring1_length: float
    ring2_length: float
    ring1_fsr: float
    ring2_fsr: float
    vernier_fsr: float
    vernier_factor: float


@dataclass(frozen=True)
class VernierResponse:
    """Response of the full Vernier filter and the component rings."""

    transmission: PortResponse
    ring1: PortResponse
    ring2: PortResponse

    @property
    def sensing_ring(self) -> PortResponse:
        """Backward-compatible alias for ``ring1``."""

        return self.ring1

    @property
    def reference_ring(self) -> PortResponse:
        """Backward-compatible alias for ``ring2``."""

        return self.ring2


@dataclass(frozen=True)
class VernierRing:
    """Two cascaded add-drop rings based on the Vernier principle.

    This follows the Luceda Academy example at the compact-model level: two ring
    resonators have slightly different FSRs, the first ring's drop output feeds the
    second ring input, and the useful transmission is the cascaded drop response.
    """

    ring1: AddDropRing
    ring2: AddDropRing
    ring1_length: float
    ring2_length: float
    n_eff_ring1: float
    n_eff_ring2: float
    n_group: float
    center_wavelength: float = 1.55
    interstage_phase: float = 0.0

    @classmethod
    def from_design(
        cls,
        *,
        center_wavelength: float = 1.55,
        ring1_fsr: float = 0.001,
        target_vernier_factor: float = 10.0,
        n_eff_ring1: float = 2.4,
        n_eff_ring2: float = 2.4,
        n_group: float = 4.5,
        coupler: Coupler | None = None,
        alpha: float = 1.0,
        sensing_fsr: float | None = None,
        n_eff_sensing: float | None = None,
        n_eff_reference: float | None = None,
    ) -> "VernierRing":
        """Synthesize ring lengths from functional Vernier parameters.

        The length synthesis mirrors the Luceda sample: the sensing ring is sized
        from its target FSR, and the reference ring uses a slightly smaller FSR so
        the two combs periodically realign.
        """

        if sensing_fsr is not None:
            ring1_fsr = sensing_fsr
        if n_eff_sensing is not None:
            n_eff_ring1 = n_eff_sensing
        if n_eff_reference is not None:
            n_eff_ring2 = n_eff_reference

        coupler = coupler or Coupler.lossless_from_t(2**-0.5)
        ring2_fsr = ring1_fsr * target_vernier_factor / (target_vernier_factor + 1)
        ring1_length = synthesize_ring_length(
            center_wavelength=center_wavelength,
            n_group=n_group,
            n_eff=n_eff_ring1,
            min_fsr=ring1_fsr,
        )
        ring2_length = synthesize_ring_length(
            center_wavelength=center_wavelength,
            n_group=n_group,
            n_eff=n_eff_ring2,
            min_fsr=ring2_fsr,
        )

        return cls(
            ring1=AddDropRing(coupler, coupler, alpha=alpha),
            ring2=AddDropRing(coupler, coupler, alpha=alpha),
            ring1_length=ring1_length,
            ring2_length=ring2_length,
            n_eff_ring1=n_eff_ring1,
            n_eff_ring2=n_eff_ring2,
            n_group=n_group,
            center_wavelength=center_wavelength,
        )

    @property
    def sensing_ring(self) -> AddDropRing:
        """Backward-compatible alias for ``ring1``."""

        return self.ring1

    @property
    def reference_ring(self) -> AddDropRing:
        """Backward-compatible alias for ``ring2``."""

        return self.ring2

    @property
    def sensing_length(self) -> float:
        """Backward-compatible alias for ``ring1_length``."""

        return self.ring1_length

    @property
    def reference_length(self) -> float:
        """Backward-compatible alias for ``ring2_length``."""

        return self.ring2_length

    @property
    def design(self) -> VernierDesign:
        ring1_fsr = fsr_from_length(
            wavelength=self.center_wavelength,
            n_group=self.n_group,
            length=self.ring1_length,
        )
        ring2_fsr = fsr_from_length(
            wavelength=self.center_wavelength,
            n_group=self.n_group,
            length=self.ring2_length,
        )
        vernier_fsr = vernier_fsr_from_ring_fsrs(ring1_fsr, ring2_fsr)
        return VernierDesign(
            ring1_length=self.ring1_length,
            ring2_length=self.ring2_length,
            ring1_fsr=ring1_fsr,
            ring2_fsr=ring2_fsr,
            vernier_fsr=vernier_fsr,
            vernier_factor=vernier_fsr / ring1_fsr,
        )

    def response_for_wavelength(self, wavelength: float) -> VernierResponse:
        ring1 = self.ring1.response_for_wavelength(
            wavelength,
            n_eff=self.n_eff_ring1,
            length=self.ring1_length,
        )
        ring2 = self.ring2.response_for_wavelength(
            wavelength,
            n_eff=self.n_eff_ring2,
            length=self.ring2_length,
        )
        transmission = (
            ring1.drop.amplitude
            * cmath.exp(1j * self.interstage_phase)
            * ring2.drop.amplitude
        )
        return VernierResponse(
            transmission=PortResponse(transmission),
            ring1=ring1.drop,
            ring2=ring2.drop,
        )

    def spectrum(self, wavelengths: Iterable[float]) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for wavelength in wavelengths:
            response = self.response_for_wavelength(wavelength)
            rows.append(
                {
                    "wavelength": wavelength,
                    "transmission_power": response.transmission.power,
                    "transmission_phase": response.transmission.phase,
                    "ring1_drop_power": response.ring1.power,
                    "ring1_drop_phase": response.ring1.phase,
                    "ring2_drop_power": response.ring2.power,
                    "ring2_drop_phase": response.ring2.phase,
                }
            )
        return rows


def synthesize_ring_length(
    *,
    center_wavelength: float,
    n_group: float,
    n_eff: float,
    min_fsr: float,
    delta_order: float = 0.0,
) -> float:
    """Choose a length satisfying an FSR target and near-center resonance."""

    length_from_fsr = center_wavelength**2 / (n_group * min_fsr)
    order = length_from_fsr * n_eff / center_wavelength
    return (math.floor(order) + 0.5 + delta_order) * center_wavelength / n_eff


def fsr_from_length(*, wavelength: float, n_group: float, length: float) -> float:
    return wavelength**2 / (n_group * length)


def vernier_fsr_from_ring_fsrs(fsr_1: float, fsr_2: float) -> float:
    if fsr_1 == fsr_2:
        return math.inf
    return abs(fsr_1 * fsr_2 / (fsr_1 - fsr_2))
