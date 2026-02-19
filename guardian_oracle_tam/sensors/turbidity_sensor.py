"""
Turbidity Sensor Driver (Simulated)

Measures water clarity in Nephelometric Turbidity Units (NTU).
This reading drives the sensor fusion confidence-weighting decision.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


# --- Threshold ---
TURBIDITY_THRESHOLD = 50.0  # NTU — above this, trust chemical over vision


@dataclass
class TurbidityReading:
    """A single turbidity measurement."""
    ntu: float                   # Nephelometric Turbidity Units
    timestamp: float = field(default_factory=time.time)
    sensor_id: str = "TURB-01"

    @property
    def is_murky(self) -> bool:
        """Returns True if turbidity exceeds the fusion threshold."""
        return self.ntu > TURBIDITY_THRESHOLD

    def __repr__(self) -> str:
        clarity = "MURKY" if self.is_murky else "CLEAR"
        return f"TurbidityReading(ntu={self.ntu:.1f} [{clarity}])"


class TurbiditySensor:
    """
    Simulated nephelometric turbidity sensor.
    
    In real hardware, this would wrap an IR-scatter photodiode sensor
    (e.g., a DFRobot SEN0189 or similar submersible probe).
    """

    def __init__(self, base_ntu: float = 10.0):
        """
        Args:
            base_ntu: Baseline turbidity level for simulation. Can be
                changed dynamically to simulate environmental shifts.
        """
        self._base_ntu = base_ntu
        self._read_count = 0

    @property
    def base_ntu(self) -> float:
        return self._base_ntu

    @base_ntu.setter
    def base_ntu(self, value: float) -> None:
        self._base_ntu = max(0.0, value)

    async def read(self) -> TurbidityReading:
        """
        Perform an asynchronous turbidity measurement.
        Simulates ~20ms optical scatter measurement.
        """
        await asyncio.sleep(0.002)  # Simulated measurement delay (accelerated)

        ntu = max(0.0, random.gauss(self._base_ntu, self._base_ntu * 0.1))
        self._read_count += 1

        return TurbidityReading(ntu=round(ntu, 1))

    def reset(self) -> None:
        """Reset read counter."""
        self._read_count = 0

    @property
    def read_count(self) -> int:
        return self._read_count
