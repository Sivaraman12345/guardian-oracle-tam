"""
Sensor Fusion — Confidence-Weighted Algorithm

Dynamically weights chemical vs. vision sensor inputs based on
water turbidity. Uses a smooth sigmoid transition rather than a hard
step function for robustness around the threshold boundary.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from sensors.turbidity_sensor import TURBIDITY_THRESHOLD


@dataclass
class FusedReading:
    """Result of the sensor fusion algorithm."""
    stress_score: float         # 0.0 (no stress) – 1.0 (max stress)
    confidence: float           # 0.0 – 1.0 overall confidence
    weight_chemical: float      # Weight assigned to chemical sensor
    weight_vision: float        # Weight assigned to vision model
    biomass_gelatinous: float   # Fused biomass estimate (kg)
    biomass_commercial: float   # Fused biomass estimate (kg)
    turbidity_ntu: float        # Raw turbidity for reference
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return (
            f"FusedReading(stress={self.stress_score:.3f}, "
            f"conf={self.confidence:.3f}, "
            f"w_chem={self.weight_chemical:.2f}, "
            f"w_vis={self.weight_vision:.2f})"
        )


def _sigmoid_weight(turbidity: float, threshold: float = TURBIDITY_THRESHOLD,
                    steepness: float = 0.15) -> float:
    """
    Compute chemical sensor weight using a sigmoid centered at the threshold.
    
    Returns a value in [0.15, 0.85]:
        - Low turbidity  → ~0.15 (trust vision)
        - High turbidity → ~0.85 (trust chemical)
    
    Args:
        turbidity: Current NTU reading.
        threshold: Center of the sigmoid transition.
        steepness: Controls how sharp the transition is.
    """
    # Sigmoid: 1 / (1 + e^(-k*(x - x0)))
    exponent = -steepness * (turbidity - threshold)
    raw_sigmoid = 1.0 / (1.0 + math.exp(exponent))

    # Scale from [0, 1] to [0.15, 0.85]
    return 0.15 + 0.70 * raw_sigmoid


def compute_chemical_stress(cortisol: float, lactate: float) -> float:
    """
    Derive a normalised stress score from chemical biomarkers.
    
    Uses a simple logistic scaling:
        - Cortisol < 10 ng/mL → low stress
        - Cortisol > 50 ng/mL → high stress
        - Lactate acts as a secondary amplifier
    
    Returns:
        float in [0.0, 1.0]
    """
    cortisol_norm = 1.0 / (1.0 + math.exp(-0.08 * (cortisol - 25.0)))
    lactate_norm = min(1.0, lactate / 8.0)
    return min(1.0, 0.7 * cortisol_norm + 0.3 * lactate_norm)


def compute_vision_stress(biomass_gelatinous: float, biomass_commercial: float) -> float:
    """
    Derive a stress score from vision-based biomass estimates.
    
    High ratio of gelatinous-to-total biomass indicates ecosystem stress.
    
    Returns:
        float in [0.0, 1.0]
    """
    total = biomass_gelatinous + biomass_commercial
    if total <= 0:
        return 0.5  # Uncertain — insufficient data
    return biomass_gelatinous / total


def fuse(
    turbidity_ntu: float,
    cortisol: float,
    lactate: float,
    biomass_gelatinous: float,
    biomass_commercial: float,
    vision_quality: float = 1.0,
) -> FusedReading:
    """
    Perform confidence-weighted sensor fusion.
    
    The algorithm computes independent stress scores from chemical and
    vision pipelines, then blends them using turbidity-driven weights.
    
    Args:
        turbidity_ntu: Current water turbidity (NTU).
        cortisol: Cortisol concentration (ng/mL).
        lactate: Lactate concentration (mmol/L).
        biomass_gelatinous: Vision-estimated gelatinous biomass (kg).
        biomass_commercial: Vision-estimated commercial biomass (kg).
        vision_quality: Camera quality score (0–1), further penalises vision.
    
    Returns:
        FusedReading with blended stress score and confidence.
    """
    # 1. Compute turbidity-driven weights
    w_chem = _sigmoid_weight(turbidity_ntu)
    w_vis = 1.0 - w_chem

    # 2. Further penalise vision if camera quality is degraded
    effective_w_vis = w_vis * vision_quality
    total_w = w_chem + effective_w_vis
    if total_w > 0:
        w_chem_norm = w_chem / total_w
        w_vis_norm = effective_w_vis / total_w
    else:
        w_chem_norm, w_vis_norm = 0.5, 0.5

    # 3. Independent stress scores
    chem_stress = compute_chemical_stress(cortisol, lactate)
    vis_stress = compute_vision_stress(biomass_gelatinous, biomass_commercial)

    # 4. Fused stress score
    fused_stress = w_chem_norm * chem_stress + w_vis_norm * vis_stress

    # 5. Confidence: higher when dominant sensor has a strong signal
    dominant_weight = max(w_chem_norm, w_vis_norm)
    confidence = dominant_weight * (0.6 + 0.4 * vision_quality)

    # 6. Fused biomass (vision-weighted — chemical can't estimate biomass directly)
    fused_gel = biomass_gelatinous
    fused_com = biomass_commercial

    return FusedReading(
        stress_score=round(fused_stress, 4),
        confidence=round(confidence, 4),
        weight_chemical=round(w_chem_norm, 4),
        weight_vision=round(w_vis_norm, 4),
        biomass_gelatinous=round(fused_gel, 2),
        biomass_commercial=round(fused_com, 2),
        turbidity_ntu=round(turbidity_ntu, 1),
    )
