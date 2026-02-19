import React from "react";
import { ShieldAlert, Zap } from "lucide-react";

export default function EscapeReflex({ active, cortisol }) {
    if (!active) return null;

    return (
        <div className="animate-alert-pulse border-t-2 border-coral-red/60 bg-coral-red/10 px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
                <div className="relative">
                    <ShieldAlert className="w-6 h-6 text-coral-red animate-pulse-glow-red rounded-full" />
                </div>
                <div>
                    <p
                        className="text-sm font-bold text-coral-red tracking-wider"
                        style={{ fontFamily: "var(--font-mono)" }}
                    >
                        ECO-STRESS DETECTED. PREPARING ESCAPE HATCH.
                    </p>
                    <p className="text-[0.6rem] text-coral-red/70 mt-0.5" style={{ fontFamily: "var(--font-mono)" }}>
                        Cortisol {cortisol.toFixed(1)} ng/mL exceeds safe threshold (25.0 ng/mL)
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-alert" />
                <span
                    className="text-[0.65rem] text-amber-alert font-semibold tracking-wider"
                    style={{ fontFamily: "var(--font-mono)" }}
                >
                    JETSON GPU ACTIVE
                </span>
            </div>
        </div>
    );
}
