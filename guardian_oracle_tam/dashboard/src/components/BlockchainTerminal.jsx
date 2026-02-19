import React, { useRef, useEffect } from "react";
import { Terminal, Hash, Send, Shield } from "lucide-react";

const TYPE_CFG = {
    sys: { icon: Shield, color: "#64748b" },
    info: { icon: Terminal, color: "#94a3b8" },
    dim: { icon: Terminal, color: "#475569" },
    alert: { icon: Terminal, color: "#f43f5e" },
    state: { icon: Terminal, color: "#22d3ee" },
    merkle: { icon: Hash, color: "#a78bfa" },
    hash: { icon: Hash, color: "#22d3ee" },
    tx: { icon: Send, color: "#10b981" },
};

export default function BlockchainTerminal({ logs, lastMerkleRoot, proofCount }) {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="panel p-5 flex flex-col h-full">
            <div className="panel-header flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-cyan-glow" />
                Blockchain Oracle Terminal
            </div>

            {/* Scrolling log */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto terminal-log pr-1 space-y-0.5 min-h-0"
                style={{ maxHeight: "calc(100% - 100px)" }}
            >
                {logs.map((entry, i) => {
                    const cfg = TYPE_CFG[entry.type] || TYPE_CFG.info;
                    const Icon = cfg.icon;
                    const isHash = entry.type === "hash";

                    return (
                        <div
                            key={i}
                            className={`log-entry flex items-start gap-1.5 py-0.5 px-1 rounded ${entry.type === "alert" ? "bg-coral-red/5" : ""
                                } ${entry.type === "tx" ? "bg-emerald-900/10" : ""}`}
                            style={{ animationDelay: `${(i % 5) * 40}ms` }}
                        >
                            <span
                                className="text-[0.55rem] text-slate-data shrink-0 mt-0.5 tabular-nums"
                                style={{ fontFamily: "var(--font-mono)" }}
                            >
                                {entry.time}
                            </span>
                            <Icon className="w-3 h-3 shrink-0 mt-0.5" style={{ color: cfg.color }} />
                            <span
                                className={`break-all ${isHash ? "animate-hash-reveal" : ""}`}
                                style={{ color: cfg.color }}
                            >
                                {entry.text}
                            </span>
                        </div>
                    );
                })}
                {/* Blinking cursor */}
                <div className="flex items-center gap-1 py-0.5 px-1">
                    <span className="text-[0.55rem] text-slate-data tabular-nums" style={{ fontFamily: "var(--font-mono)" }}>
                        &gt;
                    </span>
                    <span className="inline-block w-2 h-3.5 animate-type-cursor" />
                </div>
            </div>

            {/* Footer stats */}
            <div className="mt-3 pt-3 border-t border-panel-border">
                {lastMerkleRoot ? (
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-1.5">
                            <Hash className="w-3 h-3 text-cyan-glow" />
                            <span className="text-[0.6rem] text-slate-label" style={{ fontFamily: "var(--font-mono)" }}>
                                LAST MERKLE ROOT
                            </span>
                        </div>
                        <div
                            className="text-[0.6rem] text-cyan-glow break-all bg-deep-slate rounded px-2 py-1.5 border border-panel-border animate-hash-reveal"
                            style={{ fontFamily: "var(--font-mono)" }}
                        >
                            {lastMerkleRoot}
                        </div>
                        <div className="flex justify-between text-[0.55rem] text-slate-data" style={{ fontFamily: "var(--font-mono)" }}>
                            <span>Proofs: <span className="text-cyan-glow font-semibold">{proofCount}</span></span>
                            <span>Payload: <span className="text-emerald-400 font-semibold">40 bytes</span></span>
                            <span>Link: <span className="text-emerald-400 font-semibold">100 bps</span></span>
                        </div>
                    </div>
                ) : (
                    <div className="text-[0.6rem] text-slate-data text-center py-2" style={{ fontFamily: "var(--font-mono)" }}>
                        Awaiting first Merkle proof...
                    </div>
                )}
            </div>
        </div>
    );
}
