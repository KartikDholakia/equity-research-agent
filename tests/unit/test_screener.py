"""Unit tests for data/screener.py — Screener.in scraper.

requests.get and time.sleep are patched directly — no real network or delays.
"""
from unittest.mock import MagicMock, patch

import pytest

from data.screener import (
    _ticker_to_slug,
    _trend,
    fetch_fii_dii_trends,
    fetch_promoter_holding,
)

pytestmark = pytest.mark.unit

# ── Minimal HTML that mimics the Screener.in shareholding section ─────────────

_SHAREHOLDING_HTML = """\
<html><body>
  <section id="shareholding">
    <table>
      <tr><th>Shareholder</th><th>Dec 2023</th><th>Sep 2023</th><th>Jun 2023</th></tr>
      <tr><td>Promoters</td><td>74.15</td><td>74.15</td><td>74.15</td></tr>
      <tr><td>FIIs</td><td>10.82</td><td>10.50</td><td>9.80</td></tr>
      <tr><td>DIIs</td><td>7.30</td><td>7.80</td><td>8.00</td></tr>
      <tr><td>Pledged %</td><td>0.00</td><td>0.00</td><td>0.00</td></tr>
    </table>
  </section>
</body></html>
"""

_HIGH_PLEDGE_HTML = """\
<html><body>
  <section id="shareholding">
    <table>
      <tr><th>Shareholder</th><th>Dec 2023</th><th>Sep 2023</th></tr>
      <tr><td>Promoters</td><td>45.00</td><td>45.00</td></tr>
      <tr><td>Pledged %</td><td>35.50</td><td>34.00</td></tr>
      <tr><td>FIIs</td><td>5.00</td><td>6.00</td></tr>
      <tr><td>DIIs</td><td>3.00</td><td>3.50</td></tr>
    </table>
  </section>
</body></html>
"""

_NO_SECTION_HTML = "<html><body><p>Company not found</p></body></html>"


def _mock_response(html: str, status: int = 200) -> MagicMock:
    """Build a mock requests.Response with .text and .raise_for_status()."""
    r = MagicMock()
    r.text = html
    if status >= 400:
        r.raise_for_status.side_effect = Exception(f"HTTP {status}")
    else:
        r.raise_for_status.return_value = None
    return r


# ── Slug conversion ───────────────────────────────────────────────────────────


def test_slug_strips_ns_suffix():
    assert _ticker_to_slug("ZOMATO.NS") == "ZOMATO"


def test_slug_strips_bo_suffix():
    assert _ticker_to_slug("RELIANCE.BO") == "RELIANCE"


def test_slug_uppercases():
    assert _ticker_to_slug("infy.ns") == "INFY"


def test_slug_no_suffix_unchanged():
    assert _ticker_to_slug("AAPL") == "AAPL"


# ── Trend helper ──────────────────────────────────────────────────────────────


def test_trend_rising():
    assert _trend([11.0, 10.5, 10.0]) == "rising"


def test_trend_falling():
    assert _trend([9.0, 9.5, 10.5]) == "falling"


def test_trend_stable():
    assert _trend([10.2, 10.1, 10.0]) == "stable"


def test_trend_single_value_is_stable():
    assert _trend([10.0]) == "stable"


def test_trend_empty_returns_none():
    assert _trend([]) is None


# ── fetch_promoter_holding ─────────────────────────────────────────────────────


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_promoter_holding_happy_path(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(_SHAREHOLDING_HTML)

    result = fetch_promoter_holding("ZOMATO.NS")

    assert result["promoter_pct"] == pytest.approx(74.15)
    assert result["pledging_pct"] == pytest.approx(0.0)
    assert "error" not in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_promoter_holding_high_pledge(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(_HIGH_PLEDGE_HTML)

    result = fetch_promoter_holding("RCOM.NS")

    assert result["pledging_pct"] == pytest.approx(35.50)
    assert "error" not in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_promoter_holding_network_failure_degrades_gracefully(mock_get, mock_sleep):
    mock_get.side_effect = ConnectionError("timeout")

    result = fetch_promoter_holding("ZOMATO.NS")

    assert result["promoter_pct"] is None
    assert result["pledging_pct"] is None
    assert "error" in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_promoter_holding_no_section_degrades_gracefully(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(_NO_SECTION_HTML)

    result = fetch_promoter_holding("ZOMATO.NS")

    assert result["promoter_pct"] is None
    assert "error" in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_promoter_holding_http_error_degrades_gracefully(mock_get, mock_sleep):
    mock_get.return_value = _mock_response("", status=404)

    result = fetch_promoter_holding("ZOMATO.NS")

    assert result["promoter_pct"] is None
    assert "error" in result


# ── fetch_fii_dii_trends ──────────────────────────────────────────────────────


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_fii_trend_happy_path(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(_SHAREHOLDING_HTML)

    result = fetch_fii_dii_trends("ZOMATO.NS")

    assert result["fii_pct"] == pytest.approx(10.82)
    assert result["dii_pct"] == pytest.approx(7.30)
    assert result["fii_trend"] == "rising"
    assert "error" not in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_fii_trend_falling(mock_get, mock_sleep):
    mock_get.return_value = _mock_response(_HIGH_PLEDGE_HTML)

    result = fetch_fii_dii_trends("RCOM.NS")

    assert result["fii_trend"] == "falling"


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_fii_trend_network_failure_degrades_gracefully(mock_get, mock_sleep):
    mock_get.side_effect = ConnectionError("timeout")

    result = fetch_fii_dii_trends("ZOMATO.NS")

    assert result["fii_pct"] is None
    assert result["dii_pct"] is None
    assert result["fii_trend"] is None
    assert "error" in result


@patch("data.screener.time.sleep")
@patch("data.screener.requests.get")
def test_sleep_is_called_before_request(mock_get, mock_sleep):
    """Rate-limiting sleep must fire before the HTTP call."""
    mock_get.return_value = _mock_response(_SHAREHOLDING_HTML)

    fetch_promoter_holding("ZOMATO.NS")

    mock_sleep.assert_called_once_with(2)
