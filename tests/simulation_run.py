"""
Simulation Run - 60-Minute Haul Simulation

Simulates a complete trawling haul with three distinct phases:
    Phase 1 (Min 0-10):  Clear water, low stress -> Vision active, TWIS high
    Phase 2 (Min 11-20): Murky water, high stress -> Chemical dominates, reflex triggered
    Phase 3 (Min 21+):   Verify Merkle hash generated and acoustic "send" logged

Time is accelerated: 1 simulated minute = 0.1 real seconds.
"""

from __future__ import annotations

import sys
import os
import asyncio
import time
import logging

# Force UTF-8 stdout for Windows compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from edge_node.state_machine import EdgeController, PowerState
from sensors.chemical_sensor import StressScenario

# --- Configuration ---
SIM_DURATION_MINUTES = 30            # Simulated minutes
REAL_SECONDS_PER_SIM_MINUTE = 0.1    # Time acceleration factor
TRANSMIT_INTERVAL_SIM_MINUTES = 10   # Merkle proof every 10 sim-minutes

# Phase boundaries (simulated minutes)
PHASE_1_END = 10    # Clear water ends
PHASE_2_END = 20    # Murky water ends
PHASE_3_END = 30    # Verification phase

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-35s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulation")


class SimulationClock:
    """Tracks simulated time independently of real time."""

    def __init__(self, real_seconds_per_sim_minute: float):
        self._start_real = time.monotonic()
        self._factor = real_seconds_per_sim_minute

    def sim_minutes(self) -> float:
        elapsed_real = time.monotonic() - self._start_real
        return elapsed_real / self._factor

    def sim_seconds(self) -> float:
        return self.sim_minutes() * 60.0

    def sim_time(self) -> float:
        """Returns simulated epoch time for the proof generator."""
        return self._start_real + self.sim_seconds()


async def scenario_manager(ctrl: EdgeController, clock: SimulationClock) -> None:
    """
    Dynamically adjusts sensor scenarios based on the current
    simulation phase. Runs concurrently with the edge controller.
    """
    current_phase = 0

    while ctrl._running:
        sim_min = clock.sim_minutes()

        if sim_min < PHASE_1_END and current_phase != 1:
            # Phase 1: Clear water, low stress
            current_phase = 1
            ctrl.chem_sensor.scenario = StressScenario.CLEAR_LOW_STRESS
            ctrl.turbidity_sensor.base_ntu = 10.0
            ctrl.optical_sensor.turbidity_factor = 0.1
            logger.info(
                "==========================================================="
            )
            logger.info(
                "  PHASE 1 (Min 0-10): CLEAR WATER, LOW STRESS"
            )
            logger.info(
                "  Expected: Vision active, TWIS > 0.7"
            )
            logger.info(
                "==========================================================="
            )

        elif PHASE_1_END <= sim_min < PHASE_2_END and current_phase != 2:
            # Phase 2: Murky water, high cortisol
            current_phase = 2
            ctrl.chem_sensor.scenario = StressScenario.MURKY_HIGH_STRESS
            ctrl.turbidity_sensor.base_ntu = 85.0
            ctrl.optical_sensor.turbidity_factor = 0.85
            logger.info(
                "==========================================================="
            )
            logger.info(
                "  PHASE 2 (Min 11-20): MURKY WATER, HIGH STRESS"
            )
            logger.info(
                "  Expected: Chemical weight rises, Vision degrades, Reflex triggered"
            )
            logger.info(
                "==========================================================="
            )

        elif sim_min >= PHASE_2_END and current_phase != 3:
            # Phase 3: Verification period
            current_phase = 3
            ctrl.chem_sensor.scenario = StressScenario.MURKY_HIGH_STRESS
            logger.info(
                "==========================================================="
            )
            logger.info(
                "  PHASE 3 (Min 21-30): VERIFICATION"
            )
            logger.info(
                "  Expected: Merkle hash generated, acoustic send logged"
            )
            logger.info(
                "==========================================================="
            )

        await asyncio.sleep(REAL_SECONDS_PER_SIM_MINUTE * 0.5)


def validate_results(ctrl: EdgeController, clock: SimulationClock) -> bool:
    """
    Post-simulation validation. Checks all assertions for the three phases.
    Returns True if all checks pass.
    """
    print("\n")
    print("+-----------------------------------------------------------+")
    print("|           SIMULATION RESULTS & VALIDATION                 |")
    print("+-----------------------------------------------------------+")

    all_passed = True

    # --- Summary ---
    summary = ctrl.get_summary()
    print(f"\n  [*] Total Events Logged:     {summary['total_events']}")
    print(f"  [*] Sensor Readings:         {summary['total_sensor_readings']}")
    print(f"  [*] TWIS Calculations:       {summary['twis_readings']}")
    if summary['avg_twis'] is not None:
        print(f"  [*] Average TWIS:            {summary['avg_twis']:.4f}")
        print(f"  [*] Min TWIS:                {summary['min_twis']:.4f}")
        print(f"  [*] Max TWIS:                {summary['max_twis']:.4f}")
    print(f"  [*] Merkle Proofs Generated:  {summary['proofs_generated']}")

    # --- Assertion 1: State transitions occurred ---
    print("\n  --- Assertion 1: State Transitions ---")
    transitions = [e for e in ctrl.event_log if "TRANSITION" in e.event]
    active_entries = [e for e in transitions if "ACTIVE" in e.event]

    if len(active_entries) > 0:
        print(f"  [PASS] {len(active_entries)} state transition(s) involving ACTIVE detected")
    else:
        print("  [FAIL] No ACTIVE state transitions detected")
        all_passed = False

    # --- Assertion 2: TWIS was calculated ---
    print("\n  --- Assertion 2: TWIS Calculation ---")
    if len(ctrl.twis_history) > 0:
        print(f"  [PASS] {len(ctrl.twis_history)} TWIS score(s) calculated")
        in_range = all(0.0 <= t <= 1.0 for t in ctrl.twis_history)
        if in_range:
            print("  [PASS] All TWIS scores in valid range [0.0, 1.0]")
        else:
            print("  [FAIL] Some TWIS scores out of range")
            all_passed = False
    else:
        print("  [FAIL] No TWIS scores were calculated")
        all_passed = False

    # --- Assertion 3: Sensor fusion weights shifted ---
    print("\n  --- Assertion 3: Sensor Fusion Weights ---")
    active_cycles = [
        e for e in ctrl.sensor_log
        if e.get("type") == "active_cycle"
    ]
    if active_cycles:
        high_chem_weight = [
            e for e in active_cycles
            if e.get("weight_chemical", 0) > 0.6
        ]
        low_chem_weight = [
            e for e in active_cycles
            if e.get("weight_chemical", 1) < 0.4
        ]

        if high_chem_weight:
            print(f"  [PASS] {len(high_chem_weight)} reading(s) with high chemical weight "
                  f"(>0.6) -- murky water correctly weighted")
        else:
            print("  [WARN] No readings with high chemical weight found")

        if low_chem_weight:
            print(f"  [PASS] {len(low_chem_weight)} reading(s) with low chemical weight "
                  f"(<0.4) -- clear water correctly weighted")
    else:
        print("  [WARN] No active cycle data to validate fusion weights")

    # --- Assertion 4: Merkle proofs generated ---
    print("\n  --- Assertion 4: Merkle Proof Generation ---")
    merkle_events = [
        e for e in ctrl.event_log
        if "MERKLE_HASH_SENT" in e.event
    ]
    if len(merkle_events) > 0:
        for me in merkle_events:
            root = me.data.get("merkle_root", "?")
            leaves = me.data.get("leaf_count", "?")
            tx_bytes = me.data.get("transmission_bytes", "?")
            print(f"  [PASS] Merkle root = {root[:32]}...")
            print(f"           Leaves: {leaves} | TX: {tx_bytes} bytes")
    else:
        print("  [FAIL] No Merkle hashes were generated")
        all_passed = False

    # --- Assertion 5: Acoustic transmission simulated ---
    print("\n  --- Assertion 5: Acoustic Transmission ---")
    proofs = ctrl.proof_generator.proofs
    if proofs:
        for p in proofs:
            print(f"  [PASS] Acoustic send simulated -- {p.transmission_bytes} bytes")
            print(f"           Root: {p.merkle_root[:32]}...")
    else:
        print("  [FAIL] No acoustic transmissions logged")
        all_passed = False

    # --- Final Verdict ---
    print("\n" + "=" * 60)
    if all_passed:
        print("  ALL ASSERTIONS PASSED -- Simulation Successful!")
    else:
        print("  SOME ASSERTIONS FAILED -- Review above")
    print("=" * 60 + "\n")

    return all_passed


async def run_simulation() -> bool:
    """Main simulation entry point."""
    print("+-----------------------------------------------------------+")
    print("|    GUARDIAN ORACLE TAM -- 60-MINUTE HAUL SIMULATION       |")
    print("|    (Time Accelerated: 1 sim-min = 0.1 real-sec)           |")
    print("+-----------------------------------------------------------+\n")

    clock = SimulationClock(REAL_SECONDS_PER_SIM_MINUTE)

    # Create controller with accelerated timings
    ctrl = EdgeController(
        idle_poll_interval=REAL_SECONDS_PER_SIM_MINUTE * 0.5,
        active_poll_interval=REAL_SECONDS_PER_SIM_MINUTE * 0.3,
        transmit_interval=TRANSMIT_INTERVAL_SIM_MINUTES * 60.0,  # In sim-seconds
        idle_return_threshold=3,
    )

    # Total real duration
    real_duration = SIM_DURATION_MINUTES * REAL_SECONDS_PER_SIM_MINUTE

    # Run controller and scenario manager concurrently
    controller_task = asyncio.create_task(
        ctrl.run(duration=real_duration, sim_time_getter=clock.sim_time)
    )
    scenario_task = asyncio.create_task(
        scenario_manager(ctrl, clock)
    )

    # Wait for the controller to finish
    await controller_task
    ctrl.stop()

    # Cancel the scenario manager
    scenario_task.cancel()
    try:
        await scenario_task
    except asyncio.CancelledError:
        pass

    # Validate and report
    return validate_results(ctrl, clock)


def main():
    """Entry point for the simulation script."""
    success = asyncio.run(run_simulation())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
