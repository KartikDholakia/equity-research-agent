"""Tests for compute_eps_cagr, compute_promoter_analysis, compute_fii_trend."""
import pytest

from tools.metrics import compute_eps_cagr, compute_fii_trend, compute_promoter_analysis


# ── compute_eps_cagr ─────────────────────────────────────────────────────────────

class TestComputeEpsCagr:
    def test_standard_growth(self):
        # 10 → 20 over 4 years = 18.92% CAGR
        result = compute_eps_cagr([20, 17, 14, 12, 10])
        assert result["cagr_pct"] == pytest.approx(18.92, abs=0.1)
        assert result["years"] == 4

    def test_single_value_returns_none(self):
        result = compute_eps_cagr([10.0])
        assert result["cagr_pct"] is None
        assert result["years"] == 1

    def test_empty_returns_none(self):
        result = compute_eps_cagr([])
        assert result["cagr_pct"] is None

    def test_consistent_growth_not_lumpy(self):
        result = compute_eps_cagr([20, 18, 16, 14, 12])
        assert result["lumpy_growth"] is False
        assert result["positive_growth_years"] == 4

    def test_lumpy_growth_flagged(self):
        result = compute_eps_cagr([10, 5, 15, 4, 12])
        assert result["lumpy_growth"] is True

    def test_negative_oldest_eps_returns_none_cagr(self):
        result = compute_eps_cagr([10, 8, -2])
        assert result["cagr_pct"] is None

    def test_negative_latest_eps_returns_none_cagr(self):
        result = compute_eps_cagr([-5, 8, 10])
        assert result["cagr_pct"] is None

    def test_two_years_computed(self):
        result = compute_eps_cagr([11, 10])
        assert result["cagr_pct"] == pytest.approx(10.0, abs=0.01)
        assert result["years"] == 1

    def test_positive_growth_years_counted(self):
        # newest first: 20 > 17 > 14 > 12 > 10 — all 4 year-on-year increases
        result = compute_eps_cagr([20, 17, 14, 12, 10])
        assert result["positive_growth_years"] == 4

    def test_zero_base_eps_counts_as_positive_growth(self):
        # Company turns from EPS=0 to profitable: should count as positive growth year
        result = compute_eps_cagr([5, 3, 0])
        # i=0: eps[0]=5 > eps[1]=3 → positive; i=1: eps[1]=3 > eps[2]=0 → positive
        assert result["positive_growth_years"] == 2

    def test_zero_to_zero_not_counted(self):
        result = compute_eps_cagr([5, 0, 0])
        # i=1: eps[1]=0 > eps[2]=0 is False → not counted
        assert result["positive_growth_years"] == 1


# ── compute_promoter_analysis ────────────────────────────────────────────────────

class TestComputePromoterAnalysis:
    def test_healthy_holding(self):
        result = compute_promoter_analysis(promoter_pct=65.0, pledging_pct=5.0)
        assert result["available"] is True
        assert result["promoter_pct"] == 65.0
        assert result["pledging_pct"] == 5.0
        assert result["flag"] is None

    def test_auto_reject_at_30_pct(self):
        result = compute_promoter_analysis(promoter_pct=55.0, pledging_pct=30.0)
        assert "AUTO-REJECT" in result["flag"]

    def test_auto_reject_above_30_pct(self):
        result = compute_promoter_analysis(promoter_pct=40.0, pledging_pct=75.0)
        assert "AUTO-REJECT" in result["flag"]
        assert "75.0" in result["flag"]

    def test_just_below_threshold_no_flag(self):
        result = compute_promoter_analysis(promoter_pct=55.0, pledging_pct=29.9)
        assert result["flag"] is None

    def test_none_promoter_returns_unavailable(self):
        result = compute_promoter_analysis(promoter_pct=None, pledging_pct=10.0)
        assert result["available"] is False
        assert "UNAVAILABLE" in result["flag"]

    def test_none_pledging_returns_unavailable(self):
        result = compute_promoter_analysis(promoter_pct=60.0, pledging_pct=None)
        assert result["available"] is False

    def test_both_none_returns_unavailable(self):
        result = compute_promoter_analysis(promoter_pct=None, pledging_pct=None)
        assert result["available"] is False
        assert "UNAVAILABLE" in result["flag"]


# ── compute_fii_trend ─────────────────────────────────────────────────────────────

class TestComputeFiiTrend:
    def test_rising_is_bullish(self):
        result = compute_fii_trend(fii_trend="rising", fii_pct=22.5)
        assert result["trend"] == "rising"
        assert result["signal"] == "bullish"
        assert "22.5" in result["note"]

    def test_falling_is_bearish(self):
        result = compute_fii_trend(fii_trend="falling", fii_pct=18.0)
        assert result["signal"] == "bearish"

    def test_stable_is_neutral(self):
        result = compute_fii_trend(fii_trend="stable", fii_pct=20.0)
        assert result["signal"] == "neutral"

    def test_none_trend_returns_neutral(self):
        result = compute_fii_trend(fii_trend=None, fii_pct=None)
        assert result["signal"] == "neutral"
        assert "unavailable" in result["note"].lower()

    def test_none_pct_omitted_from_note(self):
        result = compute_fii_trend(fii_trend="rising", fii_pct=None)
        assert "%" not in result["note"] or result["note"].count("(") == 0

    def test_unknown_trend_maps_to_neutral(self):
        result = compute_fii_trend(fii_trend="unknown_value", fii_pct=10.0)
        assert result["signal"] == "neutral"
