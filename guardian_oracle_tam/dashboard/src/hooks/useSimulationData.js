/**
 * useSimulationData — Mock data hook that drives the entire dashboard.
 *
 * Simulates the 3-phase haul cycle:
 *   Phase 1 (0-10 min):  Clear water, low stress
 *   Phase 2 (11-20 min): Murky water, high stress
 *   Phase 3 (21-30 min): Verification & Merkle proof
 */
import { useState, useEffect, useRef, useCallback } from "react";

/* ── Helpers ──────────────────────────────────────────────── */
const rand = (mean, std) => mean + (Math.random() - 0.5) * 2 * std;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/* ── Phase profiles ──────────────────────────────────────── */
const PROFILES = {
    1: { cortisol: [8, 3], lactate: [1.5, 0.5], turbidity: [12, 4], gelMean: 5, comMean: 45 },
    2: { cortisol: [55, 12], lactate: [6.5, 1.5], turbidity: [85, 10], gelMean: 30, comMean: 20 },
    3: { cortisol: [58, 10], lactate: [7, 1.5], turbidity: [80, 12], gelMean: 28, comMean: 18 },
};

const CORTISOL_LIMIT = 25.0;
const TURBIDITY_THRESHOLD = 50.0;
const SIM_CYCLE_MS = 1500;           // tick every 1.5s
const SIM_MINUTES_PER_TICK = 1;      // each tick = 1 sim-minute

/* ── Terminal log templates ──────────────────────────────── */
const TERMINAL_SEEDS = {
    idle: (c) => `[SENSORS] Cortisol ${c.toFixed(1)}ng/mL < Threshold. IDLE mode.`,
    trigger: (c) => `[SENSORS] Cortisol ${c.toFixed(1)}ng/mL > Threshold. Triggering ACTIVE.`,
    active: (t) => `[FUSION]  Turbidity ${t.toFixed(0)} NTU | Chem weight: ${t > TURBIDITY_THRESHOLD ? "HIGH" : "LOW"}`,
    merkle: (n) => `[MERKLE]  Generating Proof... Leaves: ${n}`,
    root: (h) => `[ROOT]    ${h}`,
    tx: () => `[TX]      Acoustic send simulated -- 40 bytes.`,
    twis: (v) => `[TWIS]    Score: ${v.toFixed(4)}`,
};

function fakeHash() {
    const chars = "0123456789abcdef";
    let h = "";
    for (let i = 0; i < 64; i++) h += chars[Math.floor(Math.random() * 16)];
    return h;
}

/* ── Main hook ───────────────────────────────────────────── */
export default function useSimulationData() {
    const [simMinute, setSimMinute] = useState(0);
    const [phase, setPhase] = useState(1);
    const [state, setState] = useState("IDLE");       // IDLE | ACTIVE | TRANSMIT

    const [cortisol, setCortisol] = useState(8.0);
    const [lactate, setLactate] = useState(1.5);
    const [turbidity, setTurbidity] = useState(12);
    const [twis, setTwis] = useState(0.9);
    const [weightChem, setWeightChem] = useState(0.15);
    const [weightVis, setWeightVis] = useState(0.85);
    const [visionConf, setVisionConf] = useState(0.92);
    const [biomassGel, setBiomassGel] = useState(5);
    const [biomassCom, setBiomassCom] = useState(45);

    const [cortisolHistory, setCortisolHistory] = useState([]);
    const [twisHistory, setTwisHistory] = useState([]);
    const [terminalLogs, setTerminalLogs] = useState([
        { time: "00:00", text: "[SYS]     Guardian Oracle TAM v1.0 booting...", type: "sys" },
        { time: "00:00", text: "[SYS]     Demo mode ACTIVE. Simulating sensors.", type: "sys" },
    ]);

    const [proofCount, setProofCount] = useState(0);
    const [lastMerkleRoot, setLastMerkleRoot] = useState(null);
    const [escapeReflexActive, setEscapeReflexActive] = useState(false);

    const tickRef = useRef(0);

    const addLog = useCallback((text, type = "info") => {
        const mins = String(Math.floor(tickRef.current)).padStart(2, "0");
        const secs = String(Math.floor((tickRef.current % 1) * 60)).padStart(2, "0");
        setTerminalLogs((prev) => [...prev.slice(-40), { time: `${mins}:${secs}`, text, type }]);
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            tickRef.current += SIM_MINUTES_PER_TICK;
            const t = tickRef.current;
            setSimMinute(t);

            // Determine phase
            let p = t <= 10 ? 1 : t <= 20 ? 2 : 3;
            setPhase(p);
            const prof = PROFILES[p];

            // Generate sensor data
            const cort = clamp(rand(...prof.cortisol), 0, 120);
            const lact = clamp(rand(...prof.lactate), 0, 15);
            const turb = clamp(rand(...prof.turbidity), 0, 150);
            const gel = clamp(rand(prof.gelMean, 5), 0, 80);
            const com = clamp(rand(prof.comMean, 8), 1, 100);

            setCortisol(cort);
            setLactate(lact);
            setTurbidity(turb);
            setBiomassGel(gel);
            setBiomassCom(com);

            // Sensor fusion weights (sigmoid)
            const sigmoid = 1 / (1 + Math.exp(-0.15 * (turb - TURBIDITY_THRESHOLD)));
            const wChem = 0.15 + 0.70 * sigmoid;
            const wVis = 1 - wChem;
            setWeightChem(wChem);
            setWeightVis(wVis);

            // Vision confidence degrades with turbidity
            const visConf = clamp(1.0 - turb / 100, 0.05, 0.98);
            setVisionConf(visConf);

            // TWIS
            const total = gel + com;
            const tw = total > 0 ? 1 - (gel / total) : 0;
            setTwis(tw);

            // Histories
            setCortisolHistory((prev) => [...prev.slice(-25), { min: t, value: cort }]);
            setTwisHistory((prev) => [...prev.slice(-25), { min: t, value: tw }]);

            // State machine logic
            if (cort > CORTISOL_LIMIT) {
                if (state === "IDLE") {
                    setState("ACTIVE");
                    setEscapeReflexActive(true);
                    addLog(TERMINAL_SEEDS.trigger(cort), "alert");
                    addLog(`[STATE]   IDLE -> ACTIVE. Waking Jetson GPU.`, "state");
                }
            } else {
                if (state === "ACTIVE") {
                    setState("IDLE");
                    setEscapeReflexActive(false);
                    addLog(`[STATE]   ACTIVE -> IDLE. Cortisol normalised.`, "state");
                }
            }

            // Active-state logging
            if (cort > CORTISOL_LIMIT) {
                addLog(TERMINAL_SEEDS.active(turb), "info");
                addLog(TERMINAL_SEEDS.twis(tw), tw < 0.5 ? "alert" : "info");
            } else {
                addLog(TERMINAL_SEEDS.idle(cort), "dim");
            }

            // Merkle proof every 10 sim-minutes
            if (t > 0 && t % 10 === 0) {
                const leaves = 15 + Math.floor(Math.random() * 15);
                const root = fakeHash();
                setLastMerkleRoot(root);
                setProofCount((c) => c + 1);
                setState("TRANSMIT");
                addLog(TERMINAL_SEEDS.merkle(leaves), "merkle");
                addLog(TERMINAL_SEEDS.root(root), "hash");
                addLog(TERMINAL_SEEDS.tx(), "tx");
                addLog(`[STATE]   TRANSMIT -> ACTIVE. Proof committed.`, "state");
                setTimeout(() => setState(cort > CORTISOL_LIMIT ? "ACTIVE" : "IDLE"), 600);
            }

            // Loop sim after 30 minutes
            if (t >= 30) {
                tickRef.current = 0;
                setSimMinute(0);
                setCortisolHistory([]);
                setTwisHistory([]);
                addLog(`[SYS]     Simulation cycle complete. Restarting...`, "sys");
            }
        }, SIM_CYCLE_MS);

        return () => clearInterval(interval);
    }, [state, addLog]);

    return {
        simMinute, phase, state,
        cortisol, lactate, turbidity, twis,
        weightChem, weightVis, visionConf,
        biomassGel, biomassCom,
        cortisolHistory, twisHistory, terminalLogs,
        proofCount, lastMerkleRoot, escapeReflexActive,
    };
}
