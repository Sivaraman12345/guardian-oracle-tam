"""
Chemical Sensor Driver (Simulated)

Provides simulated Cortisol and Lactate readings for marine stress detection.
In production, this would interface with electrochemical biosensors.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum


class StressScenario(Enum):
    """Pre-defined simulation scenarios for the chemical sensor."""
    CLEAR_LOW_STRESS = "clear_low_stress"
    MURKY_HIGH_STRESS = "murky_high_stress"
    TRANSITION = "transition"


@dataclass
class ChemicalReading:
    """A single reading from the chemical biosensor array."""
    cortisol_ng_ml: float       # Cortisol concentration (ng/mL)
    lactate_mmol_l: float       # Lactate concentration (mmol/L)
    timestamp: float = field(default_factory=time.time)
    sensor_id: str = "CHEM-01"

    @property
    def is_stressed(self) -> bool:
        """Quick check if readings indicate ecological stress."""
        return self.cortisol_ng_ml > CORTISOL_LIMIT

    def __repr__(self) -> str:
        return (
            f"ChemicalReading(cortisol={self.cortisol_ng_ml:.2f} ng/mL, "
            f"lactate={self.lactate_mmol_l:.2f} mmol/L)"
        )


# --- Thresholds ---
CORTISOL_LIMIT = 25.0       # ng/mL — above this triggers ACTIVE state
LACTATE_BASELINE = 2.0      # mmol/L — normal resting level


# --- Scenario Profiles ---
_PROFILES: dict[StressScenario, dict] = {
    StressScenario.CLEAR_LOW_STRESS: {
        "cortisol_mean": 8.0,   "cortisol_std": 3.0,
        "lactate_mean": 1.5,    "lactate_std": 0.5,
    },
    StressScenario.MURKY_HIGH_STRESS: {
        "cortisol_mean": 55.0,  "cortisol_std": 12.0,
        "lactate_mean": 6.5,    "lactate_std": 1.5,
    },
    StressScenario.TRANSITION: {
        "cortisol_mean": 28.0,  "cortisol_std": 8.0,
        "lactate_mean": 3.5,    "lactate_std": 1.0,
    },
}


class ChemicalSensor:
    """
    Simulated electrochemical biosensor for Cortisol and Lactate.
    
    In real hardware, this would wrap an I2C/SPI driver to an
    electrochemical impedance spectroscopy (EIS) chip.
    """

    def __init__(self, scenario: StressScenario = StressScenario.CLEAR_LOW_STRESS):
        self._scenario = scenario
        self._read_count = 0

    @property
    def scenario(self) -> StressScenario:
        return self._scenario

    @scenario.setter
    def scenario(self, value: StressScenario) -> None:
        self._scenario = value

    async def read(self) -> ChemicalReading:
        """
        Perform an asynchronous sensor read.
        Simulates ~100ms ADC acquisition time.
        """
        await asyncio.sleep(0.01)  # Simulated ADC delay (accelerated)

        profile = _PROFILES[self._scenario]
        cortisol = max(0.0, random.gauss(profile["cortisol_mean"], profile["cortisol_std"]))
        lactate = max(0.0, random.gauss(profile["lactate_mean"], profile["lactate_std"]))

        self._read_count += 1
        return ChemicalReading(
            cortisol_ng_ml=round(cortisol, 2),
            lactate_mmol_l=round(lactate, 2),
        )

    def reset(self) -> None:
        """Reset the sensor read counter."""
        self._read_count = 0

    @property
    def read_count(self) -> int:
        return self._read_count
