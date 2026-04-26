"""Series-coupled ring resonator models."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
from typing import Iterable, Sequence

from ringresonator_study.components import Coupler
from ringresonator_study.phase import round_trip_phase
from ringresonator_study.responses import PortResponse, ThroughDropResponse


@dataclass(frozen=True)
class SeriesCoupledRings:
    """Series-coupled add-drop filter.

    The current implementation evaluates the two-ring series-coupled model from
    the standard ring-resonator compendium equations. The public shape already
    accepts sequences, so adding the N-ring transfer-matrix implementation later
    will not require changing callers.
    """

    bus_input_coupler: Coupler
    ring_couplers: tuple[Coupler, ...]
    bus_output_coupler: Coupler
    alphas: tuple[float, ...]

    @classmethod
    def two_ring(
        cls,
        *,
        input_coupler: Coupler,
        ring_coupler: Coupler,
        output_coupler: Coupler,
        alpha_1: float = 1.0,
        alpha_2: float = 1.0,
    ) -> "SeriesCoupledRings":
        return cls(
            bus_input_coupler=input_coupler,
            ring_couplers=(ring_coupler,),
            bus_output_coupler=output_coupler,
            alphas=(alpha_1, alpha_2),
        )

    def __post_init__(self) -> None:
        if len(self.alphas) != len(self.ring_couplers) + 1:
            raise ValueError("number of alphas must equal number of rings")
        if len(self.alphas) != 2:
            raise NotImplementedError("only two series-coupled rings are implemented")
        if any(alpha < 0 for alpha in self.alphas):
            raise ValueError("alphas must be non-negative")

    @property
    def ring_count(self) -> int:
        return len(self.alphas)

    def amplitudes(self, phis: Sequence[float]) -> tuple[complex, complex]:
        """Return ``(through_amplitude, drop_amplitude)`` for two ring phases."""

        if len(phis) != self.ring_count:
            raise ValueError("number of phases must equal number of rings")

        alpha_1, alpha_2 = self.alphas
        phase_1 = cmath.exp(1j * phis[0])
        phase_2 = cmath.exp(1j * phis[1])

        t_1 = self.bus_input_coupler.t
        k_1 = self.bus_input_coupler.kappa
        t_2 = self.ring_couplers[0].t
        k_2 = self.ring_couplers[0].kappa
        t_3 = self.bus_output_coupler.t
        k_3 = self.bus_output_coupler.kappa

        denominator = (
            1
            - t_3 * t_2 * alpha_2 * phase_2
            - t_2 * t_1 * alpha_1 * phase_1
            + t_3 * t_1 * alpha_1 * alpha_2 * phase_1 * phase_2
        )
        through = (
            -t_1
            * k_1
            * k_1
            * alpha_1
            * phase_1
            * (t_3 * alpha_2 * phase_2 - t_2)
        ) / denominator
        drop = (
            k_3
            * k_2
            * k_1
            * (alpha_1 * alpha_2) ** 0.5
            * cmath.exp(0.5j * (phis[0] + phis[1]))
        ) / denominator
        return through, drop

    def response(self, phis: Sequence[float]) -> ThroughDropResponse:
        through, drop = self.amplitudes(phis)
        return ThroughDropResponse(
            through=PortResponse(through),
            drop=PortResponse(drop),
        )

    def response_for_wavelength(
        self,
        wavelength: float,
        *,
        n_effs: Sequence[float],
        lengths: Sequence[float],
    ) -> ThroughDropResponse:
        if len(n_effs) != self.ring_count or len(lengths) != self.ring_count:
            raise ValueError("n_effs and lengths must match the number of rings")

        phis = [
            round_trip_phase(wavelength, n_eff=n_eff, length=length)
            for n_eff, length in zip(n_effs, lengths, strict=True)
        ]
        return self.response(phis)

    def spectrum(
        self,
        wavelengths: Iterable[float],
        *,
        n_effs: Sequence[float],
        lengths: Sequence[float],
    ) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for wavelength in wavelengths:
            response = self.response_for_wavelength(
                wavelength,
                n_effs=n_effs,
                lengths=lengths,
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
