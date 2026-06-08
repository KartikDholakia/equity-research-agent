"""Screener.in scraper — promoter holding and FII/DII data for Indian stocks.

Personal use only. Requests are rate-limited to be respectful to the site.
On any scrape failure both public functions return None values with an error key
so the rest of the analysis can continue (graceful degradation, per design).
"""
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

# Review - shall we move it to constants file?
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_REQUEST_DELAY = 2  # seconds — polite interval between requests


# ── Public API ─────────────────────────────────────────────────────────────────

def fetch_promoter_holding(ticker: str) -> dict[str, Any]:
    """Return latest promoter holding % and pledging % from Screener.in.

    Pledging % is expressed as a percentage of promoter holding (not total shares),
    matching the Screener.in convention used in the auto-reject rule (>30%).
    On any failure returns None values plus an "error" key.
    """
    slug = _ticker_to_slug(ticker)
    try:
        rows = _fetch_shareholding_rows(slug)
        promoter_pct = _latest(rows, ["promoters", "promoter"])
        pledging_pct = _latest(rows, ["pledged", "pledged %", "pledge"])
        return {"promoter_pct": promoter_pct, "pledging_pct": pledging_pct}
    except Exception as exc:
        return {"promoter_pct": None, "pledging_pct": None, "error": str(exc)}


def fetch_fii_dii_trends(ticker: str) -> dict[str, Any]:
    """Return latest FII/DII holding % and FII trend direction from Screener.in.

    fii_trend is derived by comparing the latest quarter vs 3 quarters ago:
    "rising" | "falling" | "stable" (threshold ±0.5 pp to filter noise).
    On any failure returns None values plus an "error" key.
    """
    slug = _ticker_to_slug(ticker)
    try:
        rows = _fetch_shareholding_rows(slug)
        fii_values = _all_values(rows, ["fiis", "fii", "foreign institutions"])
        dii_values = _all_values(rows, ["diis", "dii", "domestic institutions"])
        return {
            "fii_pct":   fii_values[0] if fii_values else None,
            "dii_pct":   dii_values[0] if dii_values else None,
            "fii_trend": _trend(fii_values),
        }
    except Exception as exc:
        return {"fii_pct": None, "dii_pct": None, "fii_trend": None, "error": str(exc)}


# ── Private helpers ────────────────────────────────────────────────────────────

def _ticker_to_slug(ticker: str) -> str:
    """Strip .NS / .BO suffix and uppercase to get the Screener.in slug."""
    for suffix in (".NS", ".BO", ".ns", ".bo"):
        if ticker.endswith(suffix):
            return ticker[: -len(suffix)].upper()
    return ticker.upper()


def _fetch_shareholding_rows(slug: str) -> dict[str, list[float]]:
    """Fetch and parse the shareholding table for a given Screener.in slug.

    Returns a dict of lowercase label → list of quarterly values (newest first).
    Raises on network error or if the shareholding section is not found.
    """
    time.sleep(_REQUEST_DELAY)
    url = f"https://www.screener.in/company/{slug}/consolidated/"
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    section = soup.find("section", id="shareholding")
    if not section:
        raise ValueError(
            f"Shareholding section not found for '{slug}'. "
            "The slug may differ from the ticker (e.g. M&M, BAJAJ-AUTO). "
            "Verify at screener.in manually."
        )

    table = section.find("table")
    if not table:
        raise ValueError(f"No shareholding table found for '{slug}'.")

    rows: dict[str, list[float]] = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        values: list[float] = []
        for cell in cells[1:]:
            text = cell.get_text(strip=True).replace(",", "").replace("%", "").strip()
            try:
                values.append(float(text))
            except ValueError:
                pass  # date headers and empty cells
        if label and values:
            rows[label] = values

    return rows


def _latest(rows: dict[str, list[float]], labels: list[str]) -> float | None:
    """Return the most recent value (index 0) for the first matching label."""
    values = _all_values(rows, labels)
    return values[0] if values else None


def _all_values(rows: dict[str, list[float]], labels: list[str]) -> list[float]:
    """Return all quarterly values for the first matching label."""
    for label in labels:
        if label in rows:
            return rows[label]
    return []


def _trend(values: list[float]) -> str | None:
    """Compare latest vs 3 quarters ago; return 'rising', 'falling', or 'stable'."""
    if not values:
        return None
    if len(values) < 2:
        return "stable"
    reference = values[min(2, len(values) - 1)]
    diff = values[0] - reference
    if diff > 0.5:
        return "rising"
    if diff < -0.5:
        return "falling"
    return "stable"
