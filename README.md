# Guardian Oracle TAM — Release v1.0

**Edge-AI Smart Trawling Net for Ecological Stress Detection & Insurance Oracle Verification**

The Guardian Oracle TAM is an underwater edge-computing system that monitors marine ecological health in real time. It calculates a **Trophic-Web Integrity Score (TWIS)** using fused sensor data and cryptographically commits proof-of-observation to a blockchain oracle for insurance smart-contract verification.

---

## How to Run

### Docker (Recommended)

```bash
# Build the container
docker build -t guardian-oracle-tam:1.0 .

# Run in demo mode (demo_mode.flag is included by default)
docker run --rm guardian-oracle-tam:1.0

# Run in production mode (remove the flag)
docker run --rm -e REMOVE_DEMO_FLAG=1 guardian-oracle-tam:1.0
```

### Local (Python 3.11+)

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests first, then start the application
bash production_launcher.sh

# Or run manually:
python -m pytest tests/ -v          # Unit tests
python tests/simulation_run.py      # 60-minute haul simulation
python main.py                      # Start the Edge Node
```

### Demo vs Production Mode

| Mode | Trigger | Behaviour |
|---|---|---|
| **Demo** | `demo_mode.flag` file present | Loops simulated sensor data through 3 phases (clear → murky → verify) in ~3 seconds |
| **Production** | `demo_mode.flag` deleted | Polls real sensors indefinitely, runs until Ctrl+C |

---

## Simulation Results

The system has been verified with a full **60-minute simulated haul** (time-accelerated). Key metrics:

| Metric | Result |
|---|---|
| TWIS Calculations | 23 scored across 3 phases |
| Average TWIS | 0.8434 (healthy ecosystem baseline) |
| TWIS Range | 0.2136 – 1.0000 |
| State Transitions | 6 (IDLE → ACTIVE → TRANSMIT cycles) |
| Merkle Proofs Generated | 2 (at 10-min intervals) |
| Acoustic Payload Size | **40 bytes** per proof (32-byte hash + 8-byte header) |
| Acoustic TX Time | ~3.2s at 100 bps |
| Simulated Inference Latency | **< 200ms** per frame (CNN-LSTM on Jetson GPU) |
| Unit Tests | **16/16 passed** (11 TWIS + 5 escape reflex) |

### Phase Breakdown

1. **Min 0–10 (Clear Water):** System in IDLE, low cortisol (3–11 ng/mL), vision sensor trusted (weight > 0.85)
2. **Min 11–20 (Murky Water):** Cortisol spike triggered IDLE → ACTIVE, chemical sensor weight > 0.93, GPU woke and ran vision AI
3. **Min 21–30 (Verification):** Second Merkle proof generated (27 leaves), acoustic transmission simulated, all hashes committed

---

## Architecture

Full architecture documentation with Mermaid diagrams is available at:

**[docs/architecture.md](docs/architecture.md)**

Diagrams included:
- System data-flow (Sensors → Edge Node → Acoustic Modem → Blockchain)
- Power state machine (IDLE → ACTIVE → TRANSMIT)
- Sensor fusion confidence-weighting decision tree
- Oracle store-and-forward sequence diagram

### Tech Stack

| Layer | Technology |
|---|---|
| Edge Logic | Python 3.11+ / `asyncio` |
| AI Inference | PyTorch (simulated CNN-LSTM) |
| Sensor Fusion | Sigmoid-weighted confidence algorithm |
| Cryptographic Proof | SHA-256 Merkle tree |
| Blockchain Oracle | Solidity 0.8.x (`ITWISOracle` interface) |
| Testing | `pytest` + 60-min haul simulation |

---

## Project Structure

```
guardian_oracle_tam/
├── main.py                    # Application entry point
├── Dockerfile                 # Production container
├── production_launcher.sh     # Test-gated launcher script
├── requirements.txt           # Python dependencies
├── demo_mode.flag             # Presence enables demo mode
├── README.md                  # This file
├── docs/
│   └── architecture.md        # Full architecture & Mermaid diagrams
├── edge_node/
│   ├── state_machine.py       # Asyncio wake-on-event controller
│   └── twis.py                # TWIS score calculation
├── sensors/
│   ├── chemical_sensor.py     # Cortisol / Lactate simulation
│   ├── optical_sensor.py      # Camera frame simulation
│   └── turbidity_sensor.py    # Turbidity (NTU) simulation
├── ai_models/
│   ├── sensor_fusion.py       # Confidence-weighted fusion
│   └── vision_model.py        # Simulated CNN-LSTM
├── blockchain/
│   ├── proof_generator.py     # Merkle tree & compact proof
│   └── oracle_interface.sol   # Solidity oracle contract
└── tests/
    ├── test_twis.py            # TWIS unit tests (11 cases)
    ├── test_escape_reflex.py   # State transition tests (5 cases)
    └── simulation_run.py       # 60-minute haul simulation
```

---

## License

Proprietary — Guardian Oracle Team. All rights reserved.
