"""Response containers with explicit amplitude, power, and phase."""

from __future__ import annotations

from dataclasses import dataclass
import math


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
class AddDropResponse:
    """Through/drop response for an add-drop ring."""

    through: PortResponse
    drop: PortResponse

    def as_dict(self) -> dict[str, PortResponse]:
        return {
            "through": self.through,
            "drop": self.drop,
        }

    def __getitem__(self, port: str) -> PortResponse:
        return self.as_dict()[port]


@dataclass(frozen=True)
class ThroughDropResponse:
    """Generic two-port filter response with through/drop outputs."""

    through: PortResponse
    drop: PortResponse

    def as_dict(self) -> dict[str, PortResponse]:
        return {
            "through": self.through,
            "drop": self.drop,
        }

    def __getitem__(self, port: str) -> PortResponse:
        return self.as_dict()[port]
