"""
Optical Sensor Driver (Simulated)

Simulates a camera system that provides biomass estimates.
In production, frames would be fed to the Vision AI model on the Jetson GPU.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


@dataclass
class OpticalReading:
    """A single capture from the optical sensor (camera frame analysis)."""
    frame_id: int
    biomass_gelatinous: float    # kg estimate — jellyfish/ctenophores
    biomass_commercial: float    # kg estimate — fish/shrimp
    timestamp: float = field(default_factory=time.time)
    quality_score: float = 1.0   # 0.0–1.0, degrades with turbidity
    sensor_id: str = "OPT-01"

    def __repr__(self) -> str:
        return (
            f"OpticalReading(frame={self.frame_id}, "
            f"gel={self.biomass_gelatinous:.1f}kg, "
            f"com={self.biomass_commercial:.1f}kg, "
            f"quality={self.quality_score:.2f})"
        )


class OpticalSensor:
    """
    Simulated underwater camera system.
    
    Produces biomass estimates that degrade in quality as turbidity increases.
    In real hardware, this would interface with a CSI/USB camera module.
    """

    def __init__(self, turbidity_factor: float = 0.0):
        """
        Args:
            turbidity_factor: 0.0 (crystal clear) to 1.0 (fully opaque).
                Used to degrade quality_score of readings.
        """
        self._frame_counter = 0
        self._turbidity_factor = turbidity_factor

    @property
    def turbidity_factor(self) -> float:
        return self._turbidity_factor

    @turbidity_factor.setter
    def turbidity_factor(self, value: float) -> None:
        self._turbidity_factor = max(0.0, min(1.0, value))

    async def capture(
        self,
        gelatinous_mean: float = 5.0,
        commercial_mean: float = 45.0,
    ) -> OpticalReading:
        """
        Capture a frame and return biomass estimates.
        
        Simulates ~50ms frame capture + basic pre-processing.
        Quality degrades with turbidity.
        """
        await asyncio.sleep(0.005)  # Simulated capture delay (accelerated)

        self._frame_counter += 1
        quality = max(0.05, 1.0 - self._turbidity_factor)

        # Add noise — more noise when turbidity is high
        noise_scale = 1.0 + (self._turbidity_factor * 4.0)
        gel = max(0.0, random.gauss(gelatinous_mean, 2.0 * noise_scale))
        com = max(0.0, random.gauss(commercial_mean, 5.0 * noise_scale))

        return OpticalReading(
            frame_id=self._frame_counter,
            biomass_gelatinous=round(gel, 2),
            biomass_commercial=round(com, 2),
            quality_score=round(quality, 3),
        )

    def reset(self) -> None:
        """Reset frame counter."""
        self._frame_counter = 0
