"""
Unit Tests — TWIS Score Calculation

Tests the Trophic-Web Integrity Score formula for correctness,
edge cases, and boundary conditions.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from edge_node.twis import calculate_twis
import pytest


class TestTWISCalculation:
    """Tests for the TWIS formula: 1 - (B_gel / (B_gel + B_com))"""

    def test_healthy_ecosystem(self):
        """When commercial biomass dominates, TWIS should be high."""
        twis = calculate_twis(biomass_gelatinous=5.0, biomass_commercial=45.0)
        assert twis == 0.9
        assert twis > 0.7, "Healthy ecosystem should have TWIS > 0.7"

    def test_moderate_stress(self):
        """Equal biomass should give TWIS = 0.5."""
        twis = calculate_twis(biomass_gelatinous=25.0, biomass_commercial=25.0)
        assert twis == 0.5

    def test_severe_stress(self):
        """When gelatinous biomass dominates, TWIS should be low."""
        twis = calculate_twis(biomass_gelatinous=40.0, biomass_commercial=10.0)
        assert twis == 0.2
        assert twis < 0.5, "Severe stress should have TWIS < 0.5"

    def test_pure_commercial(self):
        """100% commercial biomass → TWIS = 1.0 (perfect health)."""
        twis = calculate_twis(biomass_gelatinous=0.0, biomass_commercial=100.0)
        assert twis == 1.0

    def test_pure_gelatinous(self):
        """100% gelatinous biomass → TWIS = 0.0 (maximum stress)."""
        twis = calculate_twis(biomass_gelatinous=100.0, biomass_commercial=0.0)
        assert twis == 0.0

    def test_zero_biomass_degenerate(self):
        """Both zero → TWIS = 0.0 (degenerate case, no data)."""
        twis = calculate_twis(biomass_gelatinous=0.0, biomass_commercial=0.0)
        assert twis == 0.0

    def test_small_values(self):
        """Very small values should still compute correctly."""
        twis = calculate_twis(biomass_gelatinous=0.001, biomass_commercial=0.999)
        assert 0.99 <= twis <= 1.0

    def test_large_values(self):
        """Very large values should maintain ratio accuracy."""
        twis = calculate_twis(biomass_gelatinous=5000.0, biomass_commercial=45000.0)
        assert twis == 0.9

    def test_negative_gelatinous_raises(self):
        """Negative gelatinous biomass should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_twis(biomass_gelatinous=-1.0, biomass_commercial=10.0)

    def test_negative_commercial_raises(self):
        """Negative commercial biomass should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_twis(biomass_gelatinous=10.0, biomass_commercial=-5.0)

    def test_twis_range(self):
        """TWIS should always be in [0.0, 1.0] for valid inputs."""
        import random
        random.seed(42)
        for _ in range(100):
            gel = random.uniform(0, 100)
            com = random.uniform(0, 100)
            if gel + com == 0:
                continue
            twis = calculate_twis(gel, com)
            assert 0.0 <= twis <= 1.0, f"TWIS {twis} out of range for gel={gel}, com={com}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
