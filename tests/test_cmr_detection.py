"""
Unit tests for CMR (Carcinogenic, Mutagenic, Reprotoxic) substance detection.

Tests the is_cmr_substance() function from utils module.
This is a SAFETY-CRITICAL function that must work correctly.
"""
import pytest
from utils import is_cmr_substance


class TestCMRDetection:
    """Test suite for CMR substance detection."""

    def test_none_input_returns_false(self):
        """Test that None input returns False (no H-phrases = not CMR)."""
        assert is_cmr_substance(None) is False

    def test_empty_string_returns_false(self):
        """Test that empty string returns False."""
        assert is_cmr_substance("") is False

    def test_whitespace_only_returns_false(self):
        """Test that whitespace-only string returns False."""
        assert is_cmr_substance("   ") is False

    # Test H340 - Mutagenic
    def test_h340_detected(self):
        """Test that H340 (mutagenic) is correctly identified as CMR."""
        assert is_cmr_substance("H340") is True

    def test_h340_with_other_phrases(self):
        """Test H340 mixed with other H-phrases."""
        assert is_cmr_substance("H226, H340, H332") is True

    def test_h340_lowercase(self):
        """Test H340 in lowercase (should still detect)."""
        assert is_cmr_substance("h340") is True

    def test_h340_with_suffix(self):
        """Test H340 with letter suffix (e.g., H340A)."""
        assert is_cmr_substance("H340A") is True
        assert is_cmr_substance("H340i") is True

    # Test H350 - Carcinogenic
    def test_h350_detected(self):
        """Test that H350 (carcinogenic) is correctly identified as CMR."""
        assert is_cmr_substance("H350") is True

    def test_h350_with_other_phrases(self):
        """Test H350 mixed with other H-phrases."""
        assert is_cmr_substance("H315, H350, H411") is True

    def test_h350_lowercase(self):
        """Test H350 in lowercase."""
        assert is_cmr_substance("h350") is True

    def test_h350_with_suffix(self):
        """Test H350 with letter suffix (e.g., H350i for inhalation)."""
        assert is_cmr_substance("H350i") is True
        assert is_cmr_substance("H350A") is True

    # Test H360 - Reprotoxic
    def test_h360_detected(self):
        """Test that H360 (reprotoxic) is correctly identified as CMR."""
        assert is_cmr_substance("H360") is True

    def test_h360_with_other_phrases(self):
        """Test H360 mixed with other H-phrases."""
        assert is_cmr_substance("H302, H360, H400") is True

    def test_h360_lowercase(self):
        """Test H360 in lowercase."""
        assert is_cmr_substance("h360") is True

    def test_h360_with_suffix(self):
        """Test H360 with letter suffixes (common variations)."""
        assert is_cmr_substance("H360D") is True  # May damage unborn child
        assert is_cmr_substance("H360F") is True  # May damage fertility
        assert is_cmr_substance("H360FD") is True  # May damage fertility and unborn child
        assert is_cmr_substance("H360Fd") is True  # Capital H, mixed case suffix

    # Test multiple CMR phrases
    def test_multiple_cmr_phrases(self):
        """Test substances with multiple CMR classifications."""
        assert is_cmr_substance("H340, H350") is True
        assert is_cmr_substance("H350, H360") is True
        assert is_cmr_substance("H340, H350, H360") is True

    # Test similar but NON-CMR H-phrases (should return False)
    def test_h341_not_cmr(self):
        """Test H341 (suspected mutagenic) - NOT a CMR phrase."""
        assert is_cmr_substance("H341") is False

    def test_h351_not_cmr(self):
        """Test H351 (suspected carcinogenic) - NOT a CMR phrase."""
        assert is_cmr_substance("H351") is False

    def test_h361_not_cmr(self):
        """Test H361 (suspected reprotoxic) - NOT a CMR phrase."""
        assert is_cmr_substance("H361") is False

    def test_h362_not_cmr(self):
        """Test H362 (may cause harm to breastfed children) - NOT a CMR phrase."""
        assert is_cmr_substance("H362") is False

    # Test common non-CMR substances
    def test_flammable_not_cmr(self):
        """Test flammable substance (not CMR)."""
        assert is_cmr_substance("H225, H319, H336") is False

    def test_corrosive_not_cmr(self):
        """Test corrosive substance (not CMR)."""
        assert is_cmr_substance("H314, H318") is False

    def test_toxic_not_cmr(self):
        """Test toxic substance without CMR classification."""
        assert is_cmr_substance("H301, H331, H311") is False

    def test_environmental_hazard_not_cmr(self):
        """Test environmental hazard (not CMR)."""
        assert is_cmr_substance("H400, H410, H411") is False

    # Edge cases and formatting
    def test_h_phrases_with_spaces(self):
        """Test H-phrases with extra spaces."""
        assert is_cmr_substance(" H350 ") is True
        assert is_cmr_substance("H340 , H350") is True

    def test_h_phrases_semicolon_separated(self):
        """Test H-phrases separated by semicolons."""
        assert is_cmr_substance("H226; H340; H332") is True

    def test_partial_match_prevention(self):
        """Test that partial matches don't trigger false positives."""
        # "1340" should not match "H340"
        assert is_cmr_substance("CAS: 1340-23-4") is False
        # "3500" should not match "H350"
        assert is_cmr_substance("MW: 3500") is False

    def test_real_world_benzene_example(self):
        """Test with real benzene H-phrases (known CMR substance)."""
        benzene_phrases = "Flam. Liq. 2, H225; Carc. 1A, H350; Muta. 1B, H340; STOT RE 1, H372; Asp. Tox. 1, H304"
        assert is_cmr_substance(benzene_phrases) is True

    def test_real_world_formaldehyde_example(self):
        """Test with real formaldehyde H-phrases (known CMR substance)."""
        formaldehyde_phrases = "Acute Tox. 3, H301; Acute Tox. 3, H311; Acute Tox. 3, H331; Skin Corr. 1B, H314; Skin Sens. 1, H317; Carc. 1B, H350; STOT SE 3, H335"
        assert is_cmr_substance(formaldehyde_phrases) is True

    def test_real_world_ethanol_example(self):
        """Test with real ethanol H-phrases (NOT CMR)."""
        ethanol_phrases = "Flam. Liq. 2, H225"
        assert is_cmr_substance(ethanol_phrases) is False

    def test_integer_input_converted_to_string(self):
        """Test that integer inputs are properly converted to strings."""
        # Should handle non-string inputs gracefully
        assert is_cmr_substance(340) is False  # Not "H340"
        assert is_cmr_substance(350) is False  # Not "H350"


# Run tests with: pytest tests/test_cmr_detection.py -v
# Run with coverage: pytest tests/test_cmr_detection.py --cov=utils --cov-report=term-missing
