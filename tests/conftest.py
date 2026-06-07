"""Shared pytest fixtures for all test layers.

Fixtures load from tests/fixtures/*.json so the same realistic data is used
in both unit tests (in-memory) and integration tests (HTTP mock payloads).
"""
import json
import pathlib
from typing import Any

import pytest

from tools.key_figures import extract_key_figures

_FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _load(name: str) -> Any:
    return json.loads((_FIXTURES / name).read_text())


# ── Raw API response fixtures (match FMP JSON shapes exactly) ────────────────

@pytest.fixture
def sample_income_statements() -> list[dict[str, Any]]:
    return _load("fmp_income.json")


@pytest.fixture
def sample_balance_sheets() -> list[dict[str, Any]]:
    return _load("fmp_balance.json")


@pytest.fixture
def sample_cash_flows() -> list[dict[str, Any]]:
    return _load("fmp_cashflow.json")


@pytest.fixture
def sample_key_metrics() -> list[dict[str, Any]]:
    return _load("fmp_key_metrics.json")


@pytest.fixture
def sample_earnings() -> list[dict[str, Any]]:
    return _load("fmp_earnings.json")


@pytest.fixture
def sample_price_data() -> dict[str, Any]:
    return {"price": 220.50}


# ── Derived Layer 2 fixture ───────────────────────────────────────────────────

@pytest.fixture
def sample_key_figures(
    sample_income_statements: list[dict[str, Any]],
    sample_balance_sheets: list[dict[str, Any]],
    sample_cash_flows: list[dict[str, Any]],
    sample_key_metrics: list[dict[str, Any]],
    sample_price_data: dict[str, Any],
) -> dict[str, Any]:
    """Layer 2 output derived from the fixture statements — used in agent tests."""
    return extract_key_figures(
        ticker="AAPL",
        income_statements=sample_income_statements,
        balance_sheets=sample_balance_sheets,
        cash_flows=sample_cash_flows,
        key_metrics=sample_key_metrics,
        price_data=sample_price_data,
    )
