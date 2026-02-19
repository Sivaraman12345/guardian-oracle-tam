"""
Edge Node State Machine — Hierarchical Wake-on-Event Controller

Implements the core power management and data acquisition loop using
Python asyncio. The system cycles through three states:

    IDLE → ACTIVE → TRANSMIT → ACTIVE → ... → IDLE

This is the "brain" of the Guardian Oracle TAM.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from sensors.chemical_sensor import ChemicalSensor, ChemicalReading, CORTISOL_LIMIT, StressScenario
from sensors.optical_sensor import OpticalSensor
from sensors.turbidity_sensor import TurbiditySensor, TURBIDITY_THRESHOLD
from ai_models.sensor_fusion import fuse, FusedReading
from ai_models.vision_model import VisionModel, VisionResult
from edge_node.twis import calculate_twis
from blockchain.proof_generator import ProofGenerator

logger = logging.getLogger("guardian_oracle.state_machine")


class PowerState(Enum):
    """Power management states for the edge node."""
    IDLE = auto()       # Low power — chemical sensor polling only (~50 mW)
    ACTIVE = auto()     # Full power — GPU on, vision + fusion + TWIS (~15 W)
    TRANSMIT = auto()   # Acoustic transmission — sending Merkle hash


@dataclass
class EventLogEntry:
    """A single entry in the edge node event log."""
    timestamp: float
    state: str
    event: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "state": self.state,
            "event": self.event,
            **self.data,
        }


class EdgeController:
    """
    Main edge node controller implementing the Wake-on-Event state machine.
    
    Lifecycle:
        1. Starts in IDLE — polls chemical sensor every `idle_poll_interval` seconds
        2. If cortisol exceeds CORTISOL_LIMIT → transitions to ACTIVE
        3. In ACTIVE: wakes GPU, runs vision + sensor fusion, calculates TWIS
        4. Every `transmit_interval` seconds in ACTIVE → enters TRANSMIT
        5. In TRANSMIT: builds Merkle tree, simulates acoustic send
        6. Returns to IDLE when cortisol drops below limit for
           `idle_return_threshold` consecutive readings
    """

    def __init__(
        self,
        idle_poll_interval: float = 5.0,
        active_poll_interval: float = 2.0,
        transmit_interval: float = 600.0,  # 10 minutes
        idle_return_threshold: int = 3,
    ):
        # Sensors
        self.chem_sensor = ChemicalSensor()
        self.optical_sensor = OpticalSensor()
        self.turbidity_sensor = TurbiditySensor()

        # AI
        self.vision_model = VisionModel()

        # Blockchain
        self.proof_generator = ProofGenerator()

        # State
        self._state = PowerState.IDLE
        self._running = False
        self._low_cortisol_streak = 0

        # Timing
        self._idle_poll_interval = idle_poll_interval
        self._active_poll_interval = active_poll_interval
        self._transmit_interval = transmit_interval
        self._idle_return_threshold = idle_return_threshold
        self._last_transmit_time = 0.0

        # Logs
        self.event_log: list[EventLogEntry] = []
        self.sensor_log: list[dict] = []
        self.twis_history: list[float] = []

    @property
    def state(self) -> PowerState:
        return self._state

    def _log_event(self, event: str, **data: Any) -> None:
        entry = EventLogEntry(
            timestamp=time.time(),
            state=self._state.name,
            event=event,
            data=data,
        )
        self.event_log.append(entry)
        logger.info(f"[{self._state.name}] {event} | {data}")

    def _transition(self, new_state: PowerState, reason: str) -> None:
        old_state = self._state
        self._state = new_state
        self._log_event(
            f"TRANSITION: {old_state.name} → {new_state.name}",
            reason=reason,
        )

    # ──────────────── IDLE State ────────────────

    async def _idle_loop(self, sim_time_getter=None) -> None:
        """
        Low-power polling loop. Only the chemical sensor is active.
        Transitions to ACTIVE when cortisol exceeds the limit.
        """
        self._log_event("IDLE_ENTER", power_mw=50)

        while self._running and self._state == PowerState.IDLE:
            reading: ChemicalReading = await self.chem_sensor.read()

            self.sensor_log.append({
                "type": "chemical",
                "cortisol": reading.cortisol_ng_ml,
                "lactate": reading.lactate_mmol_l,
                "timestamp": reading.timestamp,
            })

            self._log_event(
                "IDLE_POLL",
                cortisol=reading.cortisol_ng_ml,
                lactate=reading.lactate_mmol_l,
            )

            if reading.is_stressed:
                self._low_cortisol_streak = 0
                self._transition(PowerState.ACTIVE, f"Cortisol {reading.cortisol_ng_ml:.1f} > {CORTISOL_LIMIT}")
                return

            await asyncio.sleep(self._idle_poll_interval)

    # ──────────────── ACTIVE State ────────────────

    async def _active_loop(self, sim_time_getter=None) -> None:
        """
        Full-power loop. GPU is awake, running vision + fusion + TWIS.
        Transitions to TRANSMIT every 10 minutes.
        Transitions back to IDLE after 3 consecutive low-cortisol reads.
        """
        self._log_event("ACTIVE_ENTER", power_w=15)

        # Wake up the GPU and load the vision model
        if not self.vision_model.is_loaded:
            await self.vision_model.load()
            self._log_event("GPU_WAKE", model="CNN-LSTM loaded")

        while self._running and self._state == PowerState.ACTIVE:
            # 1. Read all sensors concurrently
            chem_reading, turb_reading = await asyncio.gather(
                self.chem_sensor.read(),
                self.turbidity_sensor.read(),
            )

            # 2. Update optical sensor's turbidity awareness
            self.optical_sensor.turbidity_factor = min(1.0, turb_reading.ntu / 100.0)

            # 3. Run vision model
            opt_reading = await self.optical_sensor.capture()
            vision_result: VisionResult = await self.vision_model.infer(
                frame_id=opt_reading.frame_id,
                gelatinous_hint=opt_reading.biomass_gelatinous,
                commercial_hint=opt_reading.biomass_commercial,
            )

            # 4. Sensor fusion
            fused: FusedReading = fuse(
                turbidity_ntu=turb_reading.ntu,
                cortisol=chem_reading.cortisol_ng_ml,
                lactate=chem_reading.lactate_mmol_l,
                biomass_gelatinous=vision_result.biomass_gelatinous_kg,
                biomass_commercial=vision_result.biomass_commercial_kg,
                vision_quality=opt_reading.quality_score,
            )

            # 5. Calculate TWIS
            twis = calculate_twis(
                fused.biomass_gelatinous,
                fused.biomass_commercial,
            )
            self.twis_history.append(twis)

            # 6. Log everything
            log_entry = {
                "type": "active_cycle",
                "timestamp": time.time(),
                "cortisol": chem_reading.cortisol_ng_ml,
                "lactate": chem_reading.lactate_mmol_l,
                "turbidity_ntu": turb_reading.ntu,
                "biomass_gel": fused.biomass_gelatinous,
                "biomass_com": fused.biomass_commercial,
                "stress_score": fused.stress_score,
                "confidence": fused.confidence,
                "weight_chemical": fused.weight_chemical,
                "weight_vision": fused.weight_vision,
                "twis": twis,
                "vision_inference_ms": vision_result.inference_time_ms,
            }
            self.sensor_log.append(log_entry)

            self._log_event(
                "ACTIVE_CYCLE",
                twis=twis,
                stress=fused.stress_score,
                w_chem=fused.weight_chemical,
                cortisol=chem_reading.cortisol_ng_ml,
                turbidity=turb_reading.ntu,
            )

            # 7. Check for IDLE return condition
            if not chem_reading.is_stressed:
                self._low_cortisol_streak += 1
                if self._low_cortisol_streak >= self._idle_return_threshold:
                    self.vision_model.unload()
                    self._transition(PowerState.IDLE, f"Cortisol low for {self._idle_return_threshold} consecutive reads")
                    return
            else:
                self._low_cortisol_streak = 0

            # 8. Check for TRANSMIT condition
            current_time = sim_time_getter() if sim_time_getter else time.time()
            if current_time - self._last_transmit_time >= self._transmit_interval:
                self._transition(PowerState.TRANSMIT, "Transmit interval reached")
                return

            await asyncio.sleep(self._active_poll_interval)

    # ──────────────── TRANSMIT State ────────────────

    async def _transmit_loop(self, sim_time_getter=None) -> None:
        """
        Build a Merkle tree from recent sensor logs and simulate
        acoustic transmission of the compact proof.
        """
        self._log_event("TRANSMIT_ENTER")

        # Build proof from accumulated sensor logs
        proof = self.proof_generator.build_and_send(self.sensor_log)

        self._log_event(
            "MERKLE_HASH_SENT",
            merkle_root=proof["merkle_root"],
            leaf_count=proof["leaf_count"],
            transmission_bytes=proof["transmission_bytes"],
        )

        self._last_transmit_time = sim_time_getter() if sim_time_getter else time.time()

        # Return to ACTIVE
        self._transition(PowerState.ACTIVE, "Transmission complete")

    # ──────────────── Main Run Loop ────────────────

    async def run(self, duration: float | None = None, sim_time_getter=None) -> None:
        """
        Start the edge controller event loop.
        
        Args:
            duration: Maximum run time in seconds. None = run forever.
            sim_time_getter: Optional callable returning simulated time.
        """
        self._running = True
        self._last_transmit_time = sim_time_getter() if sim_time_getter else time.time()
        start_time = time.monotonic()

        self._log_event("SYSTEM_START", duration=duration)

        try:
            while self._running:
                if duration and (time.monotonic() - start_time) >= duration:
                    self._log_event("DURATION_EXPIRED")
                    break

                if self._state == PowerState.IDLE:
                    await self._idle_loop(sim_time_getter)
                elif self._state == PowerState.ACTIVE:
                    await self._active_loop(sim_time_getter)
                elif self._state == PowerState.TRANSMIT:
                    await self._transmit_loop(sim_time_getter)

        except asyncio.CancelledError:
            self._log_event("CANCELLED")
        finally:
            self._running = False
            self._log_event("SYSTEM_STOP", total_events=len(self.event_log))

    def stop(self) -> None:
        """Signal the controller to stop after the current cycle."""
        self._running = False

    def get_summary(self) -> dict:
        """Return a summary of the haul for post-surface analysis."""
        return {
            "total_events": len(self.event_log),
            "total_sensor_readings": len(self.sensor_log),
            "twis_readings": len(self.twis_history),
            "avg_twis": round(sum(self.twis_history) / len(self.twis_history), 4) if self.twis_history else None,
            "min_twis": round(min(self.twis_history), 4) if self.twis_history else None,
            "max_twis": round(max(self.twis_history), 4) if self.twis_history else None,
            "proofs_generated": self.proof_generator.proof_count,
        }
