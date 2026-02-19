import React, { useMemo } from "react";

/**
 * TWISGauge — Large radial gauge centered in the dashboard.
 *
 * Visual rules:
 *   score > 0.8 → Cyan glow (healthy)
 *   score 0.5–0.8 → Amber (moderate stress)
 *   score < 0.5 → Coral Red (severe stress)
 */
export default function TWISGauge({ twis, biomassGel, biomassCom }) {
    const percentage = Math.round(twis * 100);

    const { color, shadow, label, bgRing } = useMemo(() => {
        if (twis >= 0.8)
            return {
                color: "#22d3ee",
                shadow: "0 0 30px rgba(34,211,238,0.4)",
                label: "HEALTHY",
                bgRing: "rgba(34,211,238,0.1)",
            };
        if (twis >= 0.5)
            return {
                color: "#f59e0b",
                shadow: "0 0 30px rgba(245,158,11,0.4)",
                label: "MODERATE STRESS",
                bgRing: "rgba(245,158,11,0.1)",
            };
        return {
            color: "#f43f5e",
            shadow: "0 0 30px rgba(244,63,94,0.4)",
            label: "SEVERE STRESS",
            bgRing: "rgba(244,63,94,0.1)",
        };
    }, [twis]);

    // SVG arc math
    const r = 88;
    const circumference = 2 * Math.PI * r;
    const offset = circumference * (1 - twis);

    return (
        <div className="panel p-6 flex flex-col items-center justify-center">
            <div className="panel-header w-full text-center">TWIS — Trophic-Web Integrity Score</div>

            {/* Gauge */}
            <div className="relative w-56 h-56 my-2" style={{ filter: `drop-shadow(${shadow})` }}>
                <svg viewBox="0 0 200 200" className="w-full h-full -rotate-90">
                    {/* Background ring */}
                    <circle
                        cx="100" cy="100" r={r}
                        fill="none"
                        stroke={bgRing}
                        strokeWidth="12"
                    />
                    {/* Active ring */}
                    <circle
                        cx="100" cy="100" r={r}
                        fill="none"
                        stroke={color}
                        strokeWidth="12"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        className="twis-ring"
                    />
                    {/* Tick marks */}
                    {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
                        const angle = (v * 360 - 90) * (Math.PI / 180);
                        const x1 = 100 + (r - 8) * Math.cos(angle);
                        const y1 = 100 + (r - 8) * Math.sin(angle);
                        const x2 = 100 + (r + 8) * Math.cos(angle);
                        const y2 = 100 + (r + 8) * Math.sin(angle);
                        return (
                            <line
                                key={v}
                                x1={x1} y1={y1} x2={x2} y2={y2}
                                stroke="#475569" strokeWidth="1.5"
                            />
                        );
                    })}
                </svg>

                {/* Center readout */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span
                        className="text-4xl font-bold tabular-nums"
                        style={{ fontFamily: "var(--font-mono)", color }}
                    >
                        {twis.toFixed(2)}
                    </span>
                    <span
                        className="text-[0.6rem] font-semibold tracking-[0.2em] mt-1"
                        style={{ fontFamily: "var(--font-mono)", color }}
                    >
                        {label}
                    </span>
                </div>
            </div>

            {/* Formula & biomass breakdown */}
            <div className="mt-3 w-full space-y-2">
                <div
                    className="text-center text-[0.6rem] text-slate-data"
                    style={{ fontFamily: "var(--font-mono)" }}
                >
                    TWIS = 1 - (B<sub>gel</sub> / (B<sub>gel</sub> + B<sub>com</sub>))
                </div>

                <div className="flex justify-between px-4">
                    <div className="text-center">
                        <div className="text-[0.6rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                            Gelatinous
                        </div>
                        <div className="text-lg font-bold text-coral-red" style={{ fontFamily: "var(--font-mono)" }}>
                            {biomassGel.toFixed(1)}
                            <span className="text-[0.5rem] text-slate-data ml-0.5">kg</span>
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-[0.6rem] text-slate-label uppercase tracking-wider" style={{ fontFamily: "var(--font-mono)" }}>
                            Commercial
                        </div>
                        <div className="text-lg font-bold text-cyan-glow" style={{ fontFamily: "var(--font-mono)" }}>
                            {biomassCom.toFixed(1)}
                            <span className="text-[0.5rem] text-slate-data ml-0.5">kg</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
