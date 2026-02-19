import React, { useMemo } from "react";
import {
    Activity,
    Droplets,
    Eye,
    FlaskConical,
    Gauge,
    Zap,
} from "lucide-react";

/* ── State badge ─────────────────────────────────────────── */
function StateBadge({ state }) {
    const states = ["IDLE", "ACTIVE", "TRANSMIT"];
    const cfg = {
        IDLE: { bg: "bg-cyan-dim/40", text: "text-cyan-glow", border: "border-cyan-muted", glow: "animate-breathe" },
        ACTIVE: { bg: "bg-amber-muted/40", text: "text-amber-alert", border: "border-amber-alert/40", glow: "animate-pulse-glow-amber" },
        TRANSMIT: { bg: "bg-cyan-dim/40", text: "text-cyan-glow", border: "border-cyan-glow/40", glow: "animate-pulse-glow" },
    };
    return (
        <div className="flex items-center gap-1.5 mb-4">
            {states.map((s, i) => {
                const active = s === state;
                const c = active ? cfg[s] : { bg: "bg-deep-slate", text: "text-slate-data", border: "border-panel-border", glow: "" };
                return (
                    <React.Fragment key={s}>
                        <div
                            className={`px-3 py-1.5 rounded-md text-[0.65rem] font-bold tracking-wider border ${c.bg} ${c.text} ${c.border} ${active ? c.glow : ""}`}
                            style={{ fontFamily: "var(--font-mono)" }}
                        >
                            {s}
                        </div>
                        {i < states.length - 1 && (
                            <span className="text-slate-data text-[0.5rem]">&#9654;</span>
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
}

/* ── Inline mini bar ─────────────────────────────────────── */
function MiniBar({ value, max, color, label }) {
    const pct = Math.min(100, (value / max) * 100);
    return (
        <div className="flex items-center gap-2 mb-2">
            <span
                className="w-20 text-[0.6rem] text-slate-label shrink-0 text-right"
                style={{ fontFamily: "var(--font-mono)" }}
            >
                {label}
            </span>
            <div className="flex-1 h-2 rounded-full bg-deep-slate overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                />
            </div>
            <span
                className="w-14 text-[0.65rem] font-semibold tabular-nums text-right"
                style={{ fontFamily: "var(--font-mono)", color }}
            >
                {typeof value === "number" ? value.toFixed(1) : value}
            </span>
        </div>
    );
}

/* ── Cortisol spark chart ────────────────────────────────── */
function CortisolChart({ history }) {
    if (!history.length) return null;
    const max = Math.max(80, ...history.map((h) => h.value));
    const w = 280;
    const h = 64;
    const step = w / Math.max(history.length - 1, 1);

    const points = history.map((p, i) => {
        const x = i * step;
        const y = h - (p.value / max) * h;
        return `${x},${y}`;
    });

    const threshold25 = h - (25 / max) * h;

    return (
        <div className="mt-3 mb-1">
            <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: 64 }}>
                {/* Threshold line */}
                <line
                    x1="0" y1={threshold25} x2={w} y2={threshold25}
                    stroke="#f43f5e" strokeWidth="0.7" strokeDasharray="4 3" opacity="0.5"
                />
                <text x={w - 2} y={threshold25 - 3} textAnchor="end" fill="#f43f5e" fontSize="6" opacity="0.7">
                    25 ng/mL
                </text>

                {/* Area fill */}
                <polygon
                    points={`0,${h} ${points.join(" ")} ${w},${h}`}
                    className="fill-cyan-glow/10"
                />

                {/* Line */}
                <polyline
                    points={points.join(" ")}
                    fill="none"
                    stroke="#22d3ee"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                />

                {/* Current dot */}
                {history.length > 0 && (() => {
                    const last = history[history.length - 1];
                    const lx = (history.length - 1) * step;
                    const ly = h - (last.value / max) * h;
                    const dotColor = last.value > 25 ? "#f43f5e" : "#22d3ee";
                    return (
                        <circle cx={lx} cy={ly} r="3" fill={dotColor} className="animate-breathe" />
                    );
                })()}
            </svg>
        </div>
    );
}

/* ── Main panel ──────────────────────────────────────────── */
export default function SensorFusion({
    state,
    cortisol,
    lactate,
    turbidity,
    weightChem,
    weightVis,
    visionConf,
    cortisolHistory,
}) {
    const cortisolColor = cortisol > 25 ? "#f43f5e" : "#22d3ee";

    return (
        <div className="panel p-5 flex flex-col h-full">
            <div className="panel-header flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-cyan-glow" />
                Sensor Fusion &amp; Telemetry
            </div>

            {/* State machine */}
            <StateBadge state={state} />

            {/* Chemical Data */}
            <div className="flex items-center gap-1.5 mb-2 mt-1">
                <FlaskConical className="w-3.5 h-3.5 text-cyan-glow" />
                <span className="text-[0.65rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                    Chemical Telemetry
                </span>
            </div>

            <MiniBar value={cortisol} max={100} color={cortisolColor} label="Cortisol" />
            <MiniBar value={lactate} max={12} color="#a78bfa" label="Lactate" />

            <CortisolChart history={cortisolHistory} />

            {/* Divider */}
            <div className="border-t border-panel-border my-3" />

            {/* Turbidity + Vision */}
            <div className="flex items-center gap-1.5 mb-2">
                <Droplets className="w-3.5 h-3.5 text-amber-alert" />
                <span className="text-[0.65rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                    Optical / Turbidity
                </span>
            </div>

            <MiniBar value={turbidity} max={150} color="#f59e0b" label="NTU" />

            <div className="flex items-center gap-1.5 mb-2">
                <Eye className="w-3.5 h-3.5 text-cyan-glow" />
                <span className="text-[0.65rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                    AI Vision Confidence
                </span>
            </div>

            <MiniBar value={(visionConf * 100)} max={100} color={visionConf > 0.5 ? "#22d3ee" : "#f43f5e"} label="Conf %" />

            {/* Divider */}
            <div className="border-t border-panel-border my-3" />

            {/* Fusion weights */}
            <div className="flex items-center gap-1.5 mb-2">
                <Gauge className="w-3.5 h-3.5 text-cyan-glow" />
                <span className="text-[0.65rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                    Fusion Weights
                </span>
            </div>

            <div className="flex gap-2">
                <div className="flex-1 rounded-lg bg-deep-slate px-3 py-2 border border-panel-border">
                    <div className="text-[0.55rem] text-slate-label tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                        CHEMICAL
                    </div>
                    <div
                        className="text-xl font-bold tabular-nums"
                        style={{ fontFamily: "var(--font-mono)", color: weightChem > 0.6 ? "#f59e0b" : "#22d3ee" }}
                    >
                        {(weightChem * 100).toFixed(0)}%
                    </div>
                </div>
                <div className="flex-1 rounded-lg bg-deep-slate px-3 py-2 border border-panel-border">
                    <div className="text-[0.55rem] text-slate-label tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                        VISION
                    </div>
                    <div
                        className="text-xl font-bold tabular-nums"
                        style={{ fontFamily: "var(--font-mono)", color: weightVis > 0.4 ? "#22d3ee" : "#64748b" }}
                    >
                        {(weightVis * 100).toFixed(0)}%
                    </div>
                </div>
            </div>
        </div>
    );
}
