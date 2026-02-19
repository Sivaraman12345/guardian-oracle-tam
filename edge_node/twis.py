"""
TWIS — Trophic-Web Integrity Score Calculator

The core ecological metric for the Guardian Oracle TAM system.
Quantifies the health of the trophic web based on the ratio of
gelatinous (jellyfish/ctenophores) to commercial (fish/shrimp) biomass.
"""

from __future__ import annotations


def calculate_twis(biomass_gelatinous: float, biomass_commercial: float) -> float:
    """
    Calculate the Trophic-Web Integrity Score.
    
    Formula:
        TWIS = 1 - (B_gelatinous / (B_gelatinous + B_commercial))
    
    Interpretation:
        1.0  = Perfectly healthy — no gelatinous biomass
        0.5  = Moderate stress — equal biomass
        0.0  = Severe stress — fully gelatinous-dominated
    
    Args:
        biomass_gelatinous: Estimated gelatinous biomass (kg). Must be ≥ 0.
        biomass_commercial: Estimated commercial biomass (kg). Must be ≥ 0.
    
    Returns:
        TWIS score in [0.0, 1.0]. Returns 0.0 if both inputs are zero
        (degenerate case — no biomass detected).
    
    Raises:
        ValueError: If either biomass value is negative.
    """
    if biomass_gelatinous < 0 or biomass_commercial < 0:
        raise ValueError(
            f"Biomass values must be non-negative. "
            f"Got gelatinous={biomass_gelatinous}, commercial={biomass_commercial}"
        )

    total = biomass_gelatinous + biomass_commercial

    if total == 0.0:
        return 0.0  # Degenerate: no biomass detected

    return round(1.0 - (biomass_gelatinous / total), 4)
