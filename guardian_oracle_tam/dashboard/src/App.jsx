import React from "react";
import useSimulationData from "./hooks/useSimulationData";
import Header from "./components/Header";
import TWISGauge from "./components/TWISGauge";
import SensorFusion from "./components/SensorFusion";
import BlockchainTerminal from "./components/BlockchainTerminal";
import EscapeReflex from "./components/EscapeReflex";

export default function App() {
  const sim = useSimulationData();

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* ─── Header ──────────────────────────────────────── */}
      <Header
        state={sim.state}
        phase={sim.phase}
        proofCount={sim.proofCount}
      />

      {/* ─── Main grid ───────────────────────────────────── */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-4 p-4 overflow-hidden min-h-0">
        {/* Left: Sensor Fusion */}
        <SensorFusion
          state={sim.state}
          cortisol={sim.cortisol}
          lactate={sim.lactate}
          turbidity={sim.turbidity}
          weightChem={sim.weightChem}
          weightVis={sim.weightVis}
          visionConf={sim.visionConf}
          cortisolHistory={sim.cortisolHistory}
        />

        {/* Center: TWIS Gauge */}
        <TWISGauge
          twis={sim.twis}
          biomassGel={sim.biomassGel}
          biomassCom={sim.biomassCom}
        />

        {/* Right: Blockchain Terminal */}
        <BlockchainTerminal
          logs={sim.terminalLogs}
          lastMerkleRoot={sim.lastMerkleRoot}
          proofCount={sim.proofCount}
        />
      </main>

      {/* ─── Footer: Escape Reflex Alert ─────────────────── */}
      <EscapeReflex
        active={sim.escapeReflexActive}
        cortisol={sim.cortisol}
      />

      {/* ─── Bottom bar ────────────────────────────────────── */}
      <footer className="flex items-center justify-between px-6 py-2 border-t border-panel-border bg-panel/60 text-[0.55rem] text-slate-data"
        style={{ fontFamily: "var(--font-mono)" }}
      >
        <span>SIM MIN: <span className="text-cyan-glow font-semibold">{sim.simMinute}</span>/30</span>
        <span>TWIS AVG: <span className="text-cyan-glow font-semibold">{sim.twis.toFixed(4)}</span></span>
        <span>MERKLE PROOFS: <span className="text-cyan-glow font-semibold">{sim.proofCount}</span></span>
        <span className="text-slate-data/50">Guardian Oracle TAM v1.0 &copy; 2026</span>
      </footer>
    </div>
  );
}
