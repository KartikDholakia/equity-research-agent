"""Unit tests for tools/metrics.py — Layer 3 compute functions.

All tests are pure Python: no network calls, no API keys, no LLM.
Each function gets its own class so pytest -k filtering works cleanly.
"""
import pytest

from tools.metrics import (
    compute_cash_flow_quality,
    compute_dcf,
    compute_debt_growth,
    compute_debt_ratio,
    compute_fcf_consistency,
    compute_graham,
    compute_interest_coverage,
    compute_ocf_quality,
    compute_pe_history,
    compute_peg,
    compute_receivables_growth,
    compute_revenue_cagr,
    compute_roce_trend,
    compute_roe_trend,
)

pytestmark = pytest.mark.unit


# ── compute_roe_trend ────────────────────────────────────────────────────────


class TestComputeRoeTrend:
    def test_roe_values_computed_correctly(self):
        result = compute_roe_trend([20.0, 15.0], [100.0, 100.0])
        assert result["roe_values_pct"] == [20.0, 15.0]
        assert result["avg_pct"] == 17.5

    def test_consistent_above_15_true_when_60_pct_exceed_threshold(self):
        # 3 of 5 years above 15 → exactly 60% → consistent
        result = compute_roe_trend(
            [20.0, 20.0, 20.0, 10.0, 10.0],
            [100.0, 100.0, 100.0, 100.0, 100.0],
        )
        assert result["consistent_above_15"] is True

    def test_consistent_above_15_false_when_below_60_pct(self):
        # 2 of 5 years above 15 → 40% → not consistent
        result = compute_roe_trend(
            [20.0, 20.0, 10.0, 10.0, 10.0],
            [100.0, 100.0, 100.0, 100.0, 100.0],
        )
        assert result["consistent_above_15"] is False

    def test_empty_inputs_return_safe_defaults(self):
        result = compute_roe_trend([], [])
        assert result == {"roe_values_pct": [], "avg_pct": None, "consistent_above_15": False}

    def test_zero_equity_year_is_skipped(self):
        # Second pair has zero equity — must not raise ZeroDivisionError
        result = compute_roe_trend([100.0, 100.0], [500.0, 0.0])
        assert result["roe_values_pct"] == [20.0]
        assert result["avg_pct"] == 20.0

    def test_all_zero_equity_returns_safe_defaults(self):
        result = compute_roe_trend([100.0, 100.0], [0.0, 0.0])
        assert result == {"roe_values_pct": [], "avg_pct": None, "consistent_above_15": False}


# ── compute_roce_trend ───────────────────────────────────────────────────────


class TestComputeRoceTrend:
    def test_roce_computed_correctly(self):
        # ROCE = 100 / (400 - 100) * 100 = 33.33%
        result = compute_roce_trend([100.0], [400.0], [100.0])
        assert result["roce_values_pct"] == pytest.approx([33.33], abs=0.01)
        assert result["avg_pct"] == pytest.approx(33.33, abs=0.01)

    def test_multiple_years(self):
        result = compute_roce_trend([60.0, 50.0], [400.0, 350.0], [100.0, 100.0])
        assert len(result["roce_values_pct"]) == 2
        assert result["avg_pct"] is not None

    def test_empty_inputs_return_safe_defaults(self):
        result = compute_roce_trend([], [], [])
        assert result == {"roce_values_pct": [], "avg_pct": None}

    def test_zero_capital_employed_year_is_skipped(self):
        # Second triple: ta == cl → capital employed = 0 → skip that year
        result = compute_roce_trend([100.0, 50.0], [400.0, 200.0], [100.0, 200.0])
        assert len(result["roce_values_pct"]) == 1


# ── compute_fcf_consistency ──────────────────────────────────────────────────


class TestComputeFcfConsistency:
    def test_counts_positive_fcf_years(self):
        result = compute_fcf_consistency([100.0, 200.0, -50.0, 300.0, 400.0])
        assert result["positive_years"] == 4
        assert result["total_years"] == 5

    def test_all_negative_fcf(self):
        result = compute_fcf_consistency([-100.0, -200.0])
        assert result["positive_years"] == 0
        assert result["total_years"] == 2

    def test_empty_input(self):
        result = compute_fcf_consistency([])
        assert result == {"fcf_values": [], "positive_years": 0, "total_years": 0}

    def test_fcf_values_preserved(self):
        fcfs = [100.0, -50.0, 200.0]
        result = compute_fcf_consistency(fcfs)
        assert result["fcf_values"] == fcfs


# ── compute_ocf_quality ──────────────────────────────────────────────────────


class TestComputeOcfQuality:
    def test_no_gaps_when_ocf_exceeds_net_income(self):
        # OCF > NI in first year → break immediately
        result = compute_ocf_quality([120.0, 90.0], [100.0, 80.0])
        assert result["consecutive_gaps"] == 0
        assert result["years"] == 2

    def test_one_consecutive_gap_then_break(self):
        # Year 1: OCF(70) < NI(80) → gap; Year 2: OCF(100) > NI(80) → break
        result = compute_ocf_quality([70.0, 100.0], [80.0, 80.0])
        assert result["consecutive_gaps"] == 1

    def test_counts_all_leading_gaps(self):
        result = compute_ocf_quality([50.0, 60.0, 70.0], [80.0, 90.0, 100.0])
        assert result["consecutive_gaps"] == 3

    def test_gap_broken_mid_sequence_stops_count(self):
        # Year 1: gap; Year 2: no gap (breaks); Year 3: gap — only leading run counts
        result = compute_ocf_quality([70.0, 120.0, 60.0], [80.0, 100.0, 80.0])
        assert result["consecutive_gaps"] == 1

    def test_empty_input(self):
        result = compute_ocf_quality([], [])
        assert result == {"years": 0, "consecutive_gaps": 0}


# ── compute_debt_ratio ───────────────────────────────────────────────────────


class TestComputeDebtRatio:
    def test_ratios_computed_correctly(self):
        result = compute_debt_ratio([100.0, 200.0], [50.0, 100.0])
        assert result["de_ratios"] == [2.0, 2.0]
        assert result["latest"] == 2.0

    def test_latest_is_first_element(self):
        result = compute_debt_ratio([300.0, 100.0], [100.0, 100.0])
        assert result["latest"] == 3.0  # index 0 = newest

    def test_zero_equity_year_is_skipped(self):
        result = compute_debt_ratio([100.0, 200.0], [0.0, 100.0])
        assert result["de_ratios"] == [2.0]
        assert result["latest"] == 2.0

    def test_empty_input(self):
        result = compute_debt_ratio([], [])
        assert result == {"de_ratios": [], "latest": None}


# ── compute_interest_coverage ────────────────────────────────────────────────


class TestComputeInterestCoverage:
    def test_coverage_computed_correctly(self):
        result = compute_interest_coverage([100.0, 200.0], [10.0, 20.0])
        assert result["coverage_values"] == [10.0, 10.0]
        assert result["latest"] == 10.0
        assert result["no_debt"] is False

    def test_empty_interest_expenses_signals_no_debt(self):
        result = compute_interest_coverage([100.0], [])
        assert result["no_debt"] is True
        assert result["latest"] is None

    def test_zero_interest_expense_year_is_skipped(self):
        result = compute_interest_coverage([100.0, 200.0], [10.0, 0.0])
        assert result["coverage_values"] == [10.0]

    def test_empty_operating_incomes_after_zip(self):
        # zip([], [10.0]) produces no pairs → falls into the "not pairs" guard
        # which returns no_debt=True (same as the no-interest-expense case)
        result = compute_interest_coverage([], [10.0])
        assert result["coverage_values"] == []
        assert result["latest"] is None
        assert result["no_debt"] is True


# ── compute_dcf ──────────────────────────────────────────────────────────────


class TestComputeDcf:
    def test_bull_greater_than_base_greater_than_bear(self):
        result = compute_dcf(0.05, 100.0)
        assert result["bull"] > result["base"] > result["bear"]

    def test_all_three_scenarios_are_positive(self):
        result = compute_dcf(0.05, 100.0)
        assert result["bear"] > 0
        assert result["base"] > 0
        assert result["bull"] > 0

    def test_margin_of_safety_negative_when_overvalued(self):
        # Use a very small FCF yield so DCF base << current price
        result = compute_dcf(0.001, 1000.0)
        assert result["margin_of_safety_base_pct"] < 0

    def test_margin_of_safety_positive_when_undervalued(self):
        # Use a large FCF yield so DCF base >> current price
        result = compute_dcf(0.15, 10.0)
        assert result["margin_of_safety_base_pct"] > 0

    def test_none_fcf_yield_returns_all_none(self):
        result = compute_dcf(None, 100.0)
        assert result == {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}

    def test_zero_fcf_yield_returns_all_none(self):
        result = compute_dcf(0.0, 100.0)
        assert result == {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}

    def test_negative_fcf_yield_returns_all_none(self):
        result = compute_dcf(-0.02, 100.0)
        assert result == {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}

    def test_zero_price_returns_all_none(self):
        result = compute_dcf(0.05, 0.0)
        assert result == {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}

    def test_none_price_returns_all_none(self):
        result = compute_dcf(0.05, None)
        assert result == {"bear": None, "base": None, "bull": None, "margin_of_safety_base_pct": None}


# ── compute_graham ───────────────────────────────────────────────────────────


class TestComputeGraham:
    def test_undervalued_stock_has_positive_margin_of_safety(self):
        # Graham number (100) > current price (80) → undervalued
        result = compute_graham(100.0, 80.0)
        assert result["graham_number"] == 100.0
        assert result["margin_of_safety_pct"] == pytest.approx(20.0)

    def test_overvalued_stock_has_negative_margin_of_safety(self):
        # Graham number (80) < current price (100) → overvalued
        result = compute_graham(80.0, 100.0)
        assert result["margin_of_safety_pct"] == pytest.approx(-25.0)

    def test_none_graham_number_returns_none_fields(self):
        result = compute_graham(None, 100.0)
        assert result == {"graham_number": None, "margin_of_safety_pct": None}

    def test_none_price_returns_none_fields(self):
        result = compute_graham(100.0, None)
        assert result == {"graham_number": None, "margin_of_safety_pct": None}

    def test_zero_graham_number_returns_none_fields(self):
        result = compute_graham(0.0, 100.0)
        assert result == {"graham_number": None, "margin_of_safety_pct": None}


# ── compute_peg ──────────────────────────────────────────────────────────────


class TestComputePeg:
    def test_peg_below_1_is_undervalued_growth(self):
        assert compute_peg(0.5)["interpretation"] == "undervalued_growth"
        assert compute_peg(0.99)["interpretation"] == "undervalued_growth"

    def test_peg_1_to_1_5_is_fair(self):
        assert compute_peg(1.0)["interpretation"] == "fair"
        assert compute_peg(1.4)["interpretation"] == "fair"

    def test_peg_1_5_to_2_is_slightly_expensive(self):
        assert compute_peg(1.5)["interpretation"] == "slightly_expensive"
        assert compute_peg(1.9)["interpretation"] == "slightly_expensive"

    def test_peg_2_and_above_is_expensive(self):
        assert compute_peg(2.0)["interpretation"] == "expensive"
        assert compute_peg(5.0)["interpretation"] == "expensive"

    def test_none_peg_is_unavailable(self):
        result = compute_peg(None)
        assert result == {"peg_ratio": None, "interpretation": "unavailable"}

    def test_zero_peg_is_unavailable(self):
        result = compute_peg(0.0)
        assert result == {"peg_ratio": None, "interpretation": "unavailable"}

    def test_negative_peg_is_unavailable(self):
        result = compute_peg(-1.0)
        assert result == {"peg_ratio": None, "interpretation": "unavailable"}

    def test_peg_ratio_rounded_in_output(self):
        result = compute_peg(1.2345)
        assert result["peg_ratio"] == 1.23


# ── compute_pe_history ───────────────────────────────────────────────────────


class TestComputePeHistory:
    def test_pe_values_derived_from_earnings_yields(self):
        # 1/0.04 = 25, 1/0.05 = 20
        result = compute_pe_history([0.04, 0.05])
        assert result["current_pe"] == pytest.approx(25.0, abs=0.01)
        assert result["avg_5yr_pe"] == pytest.approx(22.5, abs=0.01)

    def test_pct_vs_avg_positive_when_current_pe_above_average(self):
        # current=25, avg=20 → +25%
        result = compute_pe_history([0.04, 0.05, 0.05])
        assert result["pct_vs_avg"] > 0

    def test_pct_vs_avg_negative_when_current_pe_below_average(self):
        # current=20, avg=25 → negative
        result = compute_pe_history([0.05, 0.04, 0.04])
        assert result["pct_vs_avg"] < 0

    def test_single_yield_returns_none_fields(self):
        result = compute_pe_history([0.04])
        assert result == {"pe_values": [], "current_pe": None, "avg_5yr_pe": None, "pct_vs_avg": None}

    def test_empty_yields_returns_none_fields(self):
        result = compute_pe_history([])
        assert result == {"pe_values": [], "current_pe": None, "avg_5yr_pe": None, "pct_vs_avg": None}


# ── compute_revenue_cagr ─────────────────────────────────────────────────────


class TestComputeRevenueCagr:
    def test_cagr_computed_correctly(self):
        # newest=200, oldest=100, n=1 year → CAGR = 100%
        result = compute_revenue_cagr([200.0, 100.0])
        assert result["cagr_pct"] == pytest.approx(100.0, abs=0.01)
        assert result["years"] == 1

    def test_multi_year_cagr(self):
        # newest=121, oldest=100, n=2 → CAGR = 10%
        result = compute_revenue_cagr([121.0, 110.0, 100.0])
        assert result["cagr_pct"] == pytest.approx(10.0, abs=0.01)
        assert result["years"] == 2

    def test_single_year_returns_none_cagr(self):
        result = compute_revenue_cagr([200.0])
        assert result["cagr_pct"] is None
        assert result["years"] == 1

    def test_empty_list_returns_none_cagr(self):
        result = compute_revenue_cagr([])
        assert result["cagr_pct"] is None

    def test_zero_oldest_revenue_returns_none_cagr(self):
        result = compute_revenue_cagr([200.0, 100.0, 0.0])
        assert result["cagr_pct"] is None


# ── compute_cash_flow_quality ────────────────────────────────────────────────


class TestComputeCashFlowQuality:
    def test_zero_consecutive_gaps_no_auto_reject(self):
        # OCF > NI in first year → 0 gaps
        result = compute_cash_flow_quality([120.0, 100.0], [100.0, 80.0])
        assert result["consecutive_gaps"] == 0
        assert result["auto_reject"] is False

    def test_one_consecutive_gap_no_auto_reject(self):
        result = compute_cash_flow_quality([70.0, 120.0], [80.0, 100.0])
        assert result["consecutive_gaps"] == 1
        assert result["auto_reject"] is False

    def test_two_consecutive_gaps_triggers_auto_reject(self):
        result = compute_cash_flow_quality([70.0, 70.0, 120.0], [80.0, 80.0, 100.0])
        assert result["consecutive_gaps"] == 2
        assert result["auto_reject"] is True

    def test_three_consecutive_gaps_also_auto_reject(self):
        result = compute_cash_flow_quality([50.0, 60.0, 70.0], [80.0, 90.0, 100.0])
        assert result["consecutive_gaps"] == 3
        assert result["auto_reject"] is True

    def test_gap_broken_mid_sequence_no_false_positive(self):
        # Year 1: gap; Year 2: no gap; Year 3: gap — only leading run counts
        result = compute_cash_flow_quality([70.0, 120.0, 50.0], [80.0, 100.0, 80.0])
        assert result["consecutive_gaps"] == 1
        assert result["auto_reject"] is False

    def test_empty_input(self):
        result = compute_cash_flow_quality([], [])
        assert result == {"consecutive_gaps": 0, "auto_reject": False}


# ── compute_receivables_growth ───────────────────────────────────────────────


class TestComputeReceivablesGrowth:
    def test_fewer_than_3_data_points_returns_empty(self):
        result = compute_receivables_growth([200.0, 100.0], [1000.0, 900.0])
        assert result == {"bad_years": 0, "ratios": []}

    def test_no_flagged_years_when_receivables_grow_in_line_with_revenue(self):
        # recv: 110→100 (+10%), rev: 1100→1000 (+10%) → not flagged
        result = compute_receivables_growth([110.0, 100.0, 90.0], [1100.0, 1000.0, 900.0])
        assert result["bad_years"] == 0

    def test_flags_year_when_receivables_grow_much_faster_than_revenue(self):
        # recv: 200→100 (+100%), rev: 1100→1000 (+10%) → 100% >> 10%*1.5 → flagged
        result = compute_receivables_growth([200.0, 100.0, 90.0], [1100.0, 1000.0, 900.0])
        assert result["bad_years"] >= 1
        assert result["ratios"][0]["flagged"] is True

    def test_ratios_list_length_matches_year_pairs(self):
        # 4 data points → 3 year-pairs
        result = compute_receivables_growth(
            [120.0, 110.0, 100.0, 90.0], [1200.0, 1100.0, 1000.0, 900.0]
        )
        assert len(result["ratios"]) == 3

    def test_declining_revenue_year_not_flagged(self):
        # vg <= 0 → flagged condition requires vg > 0, so not flagged even if recv grew
        result = compute_receivables_growth([200.0, 100.0, 90.0], [900.0, 1000.0, 900.0])
        assert result["ratios"][0]["flagged"] is False


# ── compute_debt_growth ──────────────────────────────────────────────────────


class TestComputeDebtGrowth:
    def test_fewer_than_4_data_points_returns_safe_defaults(self):
        result = compute_debt_growth([200.0, 150.0, 100.0], [1000.0, 900.0, 800.0])
        assert result == {"consecutive_years": 0, "auto_reject": False, "year_flags": []}

    def test_zero_consecutive_years_no_auto_reject(self):
        # Debt shrinks while revenue grows → no flags
        result = compute_debt_growth(
            [100.0, 120.0, 150.0, 200.0], [1000.0, 900.0, 800.0, 700.0]
        )
        assert result["consecutive_years"] == 0
        assert result["auto_reject"] is False

    def test_two_consecutive_years_no_auto_reject(self):
        # Years 1 and 2: debt grows faster; Year 3: debt flat while revenue jumps → no flag
        # i=0: (200-150)/150=33% vs (1000-980)/980=2%  → True
        # i=1: (150-130)/130=15% vs (980-940)/940=4%   → True
        # i=2: (130-130)/130=0%  vs (940-800)/800=18%  → False → leading run = 2
        result = compute_debt_growth(
            [200.0, 150.0, 130.0, 130.0], [1000.0, 980.0, 940.0, 800.0]
        )
        assert result["consecutive_years"] == 2
        assert result["auto_reject"] is False

    def test_three_consecutive_years_triggers_auto_reject(self):
        # All 3 year-pairs: debt grows significantly faster than revenue
        result = compute_debt_growth(
            [400.0, 200.0, 120.0, 100.0], [1100.0, 1000.0, 950.0, 900.0]
        )
        assert result["consecutive_years"] == 3
        assert result["auto_reject"] is True

    def test_year_flags_length_matches_data_pairs(self):
        # 5 data points → 4 year-pairs
        result = compute_debt_growth(
            [500.0, 400.0, 300.0, 200.0, 100.0],
            [1100.0, 1000.0, 900.0, 800.0, 700.0],
        )
        assert len(result["year_flags"]) == 4

    def test_consecutive_count_resets_after_break(self):
        # Year 1: debt faster (flag); Year 2: revenue faster (no flag); Year 3: debt faster
        # Leading run = 1, not 2
        result = compute_debt_growth(
            [200.0, 100.0, 150.0, 100.0], [1000.0, 900.0, 800.0, 700.0]
        )
        assert result["consecutive_years"] == 1
