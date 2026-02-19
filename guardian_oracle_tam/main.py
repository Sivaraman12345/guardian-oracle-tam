"""
Guardian Oracle TAM — Main Entry Point

Runs the Edge Node controller. When `demo_mode.flag` is present in the
project root, the system loops simulated sensor data instead of
attempting to connect to real hardware.
"""
from __future__ import annotations

import streamlit as st

st.title("Guardian Oracle TAM")
st.write("System is running in demo mode")
if st.button("Run Guardian Oracle Demo"):
    st.write("Running simulation...")
    main()
    st.success("Simulation completed. Check terminal logs.")


import asyncio
import logging
import os
import sys

# Ensure guardian_oracle_tam root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from edge_node.state_machine import EdgeController, PowerState
from sensors.chemical_sensor import StressScenario

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEMO_FLAG_PATH = os.path.join(os.path.dirname(__file__), "demo_mode.flag")
IS_DEMO_MODE = os.path.exists(DEMO_FLAG_PATH)

# Timing (real-time for production, accelerated for demo)
if IS_DEMO_MODE:
    SIM_DURATION_MINUTES = 30
    REAL_SECONDS_PER_SIM_MINUTE = 0.1      # 30 sim-minutes in ~3 real seconds
    IDLE_POLL = 0.05
    ACTIVE_POLL = 0.03
    TRANSMIT_INTERVAL = 600.0               # 10 sim-minutes in sim-seconds
else:
    SIM_DURATION_MINUTES = None             # Run indefinitely
    IDLE_POLL = 5.0
    ACTIVE_POLL = 2.0
    TRANSMIT_INTERVAL = 600.0              # 10 real minutes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-35s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("guardian_oracle.main")

# ---------------------------------------------------------------------------
# Demo-mode helpers
# ---------------------------------------------------------------------------

import time as _time

class _DemoClock:
    """Accelerated clock for demo mode."""
    def __init__(self, factor: float):
        self._start = _time.monotonic()
        self._factor = factor

    def sim_minutes(self) -> float:
        return (_time.monotonic() - self._start) / self._factor

    def sim_time(self) -> float:
        return self._start + self.sim_minutes() * 60.0


async def _demo_scenario_manager(ctrl: EdgeController, clock: _DemoClock) -> None:
    """Cycles through stress scenarios during demo mode."""
    PHASE_1_END, PHASE_2_END = 10, 20
    current_phase = 0

    while ctrl._running:
        sim_min = clock.sim_minutes()

        if sim_min < PHASE_1_END and current_phase != 1:
            current_phase = 1
            ctrl.chem_sensor.scenario = StressScenario.CLEAR_LOW_STRESS
            ctrl.turbidity_sensor.base_ntu = 10.0
            ctrl.optical_sensor.turbidity_factor = 0.1
            logger.info("DEMO PHASE 1: Clear water, low stress")

        elif PHASE_1_END <= sim_min < PHASE_2_END and current_phase != 2:
            current_phase = 2
            ctrl.chem_sensor.scenario = StressScenario.MURKY_HIGH_STRESS
            ctrl.turbidity_sensor.base_ntu = 85.0
            ctrl.optical_sensor.turbidity_factor = 0.85
            logger.info("DEMO PHASE 2: Murky water, high stress")

        elif sim_min >= PHASE_2_END and current_phase != 3:
            current_phase = 3
            ctrl.chem_sensor.scenario = StressScenario.MURKY_HIGH_STRESS
            logger.info("DEMO PHASE 3: Verification & Merkle proof")

        await asyncio.sleep(REAL_SECONDS_PER_SIM_MINUTE * 0.5 if IS_DEMO_MODE else 5.0)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run() -> None:
    mode_label = "DEMO" if IS_DEMO_MODE else "PRODUCTION"
    logger.info(f"Guardian Oracle TAM v1.0 starting in {mode_label} mode")

    ctrl = EdgeController(
        idle_poll_interval=IDLE_POLL,
        active_poll_interval=ACTIVE_POLL,
        transmit_interval=TRANSMIT_INTERVAL,
        idle_return_threshold=3,
    )

    if IS_DEMO_MODE:
        clock = _DemoClock(REAL_SECONDS_PER_SIM_MINUTE)
        real_duration = SIM_DURATION_MINUTES * REAL_SECONDS_PER_SIM_MINUTE

        controller_task = asyncio.create_task(
            ctrl.run(duration=real_duration, sim_time_getter=clock.sim_time)
        )
        scenario_task = asyncio.create_task(
            _demo_scenario_manager(ctrl, clock)
        )

        await controller_task
        ctrl.stop()
        scenario_task.cancel()
        try:
            await scenario_task
        except asyncio.CancelledError:
            pass

        # Print summary
        summary = ctrl.get_summary()
        logger.info("=== DEMO RUN COMPLETE ===")
        for k, v in summary.items():
            logger.info(f"  {k}: {v}")
    else:
        # Production: run indefinitely until interrupted
        logger.info("Waiting for sensor events... (Ctrl+C to stop)")
        try:
            await ctrl.run(duration=None)
        except KeyboardInterrupt:
            ctrl.stop()
            logger.info("Shutdown requested. Dumping local logs...")
            summary = ctrl.get_summary()
            for k, v in summary.items():
                logger.info(f"  {k}: {v}")


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Guardian Oracle TAM shutdown.")


#if __name__ == "__main__":
 #   main()
 
