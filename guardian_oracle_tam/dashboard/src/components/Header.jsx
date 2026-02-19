import React from "react";
import { Anchor, Radio, Wifi, AlertTriangle } from "lucide-react";

export default function Header({ state, phase, proofCount }) {
    const stateColors = {
        IDLE: "text-cyan-glow",
        ACTIVE: "text-amber-alert",
        TRANSMIT: "text-cyan-glow",
    };

    return (
        <header className="flex items-center justify-between px-6 py-3 border-b border-panel-border bg-panel/80 backdrop-blur-md">
            {/* Left: Logo + connection */}
            <div className="flex items-center gap-5">
                <div className="flex items-center gap-2.5">
                    <Anchor className="w-7 h-7 text-cyan-glow animate-breathe" />
                    <div>
                        <h1
                            className="text-lg font-bold tracking-[0.15em] text-cyan-glow"
                            style={{ fontFamily: "var(--font-mono)" }}
                        >
                            GUARDIAN ORACLE
                        </h1>
                        <p className="text-[0.6rem] text-slate-label tracking-widest uppercase">
                            Maritime Edge-AI &bull; TAM v1.0
                        </p>
                    </div>
                </div>

                {/* Connection status */}
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-deep-slate border border-panel-border">
                    <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                    <span
                        className="text-[0.65rem] text-slate-label"
                        style={{ fontFamily: "var(--font-mono)" }}
                    >
                        Acoustic Link: 40 bytes/pkt&ensp;
                        <span className="text-emerald-400">&#9679; STABLE</span>
                    </span>
                </div>

                {/* Proof counter */}
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-deep-slate border border-panel-border">
                    <Radio className="w-3.5 h-3.5 text-cyan-glow" />
                    <span
                        className="text-[0.65rem] text-slate-label"
                        style={{ fontFamily: "var(--font-mono)" }}
                    >
                        Proofs Committed:&ensp;
                        <span className="text-cyan-glow font-semibold">{proofCount}</span>
                    </span>
                </div>
            </div>

            {/* Right: Demo mode flag */}
            <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-alert/10 border border-amber-alert/30">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-alert" />
                    <span
                        className="text-[0.65rem] text-amber-alert font-semibold tracking-wider"
                        style={{ fontFamily: "var(--font-mono)" }}
                    >
                        DEMO_MODE: ACTIVE
                    </span>
                </div>

                {/* Phase badge */}
                <div
                    className="px-3 py-1.5 rounded-lg bg-deep-slate border border-panel-border text-[0.65rem] tracking-wider"
                    style={{ fontFamily: "var(--font-mono)" }}
                >
                    <span className="text-slate-label">PHASE </span>
                    <span className="text-cyan-glow font-bold">{phase}</span>
                    <span className="text-slate-label">/3</span>
                </div>
            </div>
        </header>
    );
}
