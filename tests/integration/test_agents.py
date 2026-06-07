"""Integration tests for the LLM agent layer — Layer 4.

The Anthropic SDK is mocked via pytest-mock so no real API calls or keys
are needed. Tests verify that each agent's output matches the required
schema and that the fallback path (loop ends without submit_analysis)
also produces a valid dict.
"""
from types import SimpleNamespace
from typing import Any

import pytest

from agents import bear_case_agent, quality_agent, value_agent

pytestmark = pytest.mark.integration

_REQUIRED_KEYS = {"agent", "ticker", "signal", "score", "summary", "details", "flags", "timestamp"}
_VALID_SIGNALS = {"bullish", "neutral", "bearish"}


# ── Fake Anthropic response builders ─────────────────────────────────────────


def _submit_response(
    signal: str = "bullish",
    score: float = 7.5,
    summary: str = "• Metric A is strong. • No major red flags.",
    flags: list[str] | None = None,
) -> Any:
    """Fake SDK response that triggers the submit_analysis branch immediately."""
    tool_block = SimpleNamespace(
        type="tool_use",
        name="submit_analysis",
        id="tool_abc123",
        input={
            "signal": signal,
            "score": score,
            "summary": summary,
            "flags": flags or [],
        },
    )
    return SimpleNamespace(stop_reason="tool_use", content=[tool_block])


def _end_turn_response() -> Any:
    """Fake SDK response that ends the loop without calling submit_analysis."""
    return SimpleNamespace(stop_reason="end_turn", content=[])


# ── Schema compliance — all three agents ─────────────────────────────────────


@pytest.mark.parametrize("module,expected_agent_name", [
    (quality_agent,   "quality_agent"),
    (value_agent,     "value_agent"),
    (bear_case_agent, "bear_case_agent"),
])
class TestAgentSchemaCompliance:
    """Each test runs three times — once per agent module."""

    def _run(self, module: Any, mocker: Any, sample_key_figures: dict) -> dict:
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _submit_response()
        mocker.patch("anthropic.Anthropic", return_value=mock_client)
        return module.analyze("AAPL", sample_key_figures)

    def test_all_8_required_keys_present(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert set(result.keys()) == _REQUIRED_KEYS

    def test_signal_is_one_of_three_valid_values(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert result["signal"] in _VALID_SIGNALS

    def test_score_is_float(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert isinstance(result["score"], float)

    def test_score_is_within_0_to_10(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert 0.0 <= result["score"] <= 10.0

    def test_flags_is_a_list(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert isinstance(result["flags"], list)

    def test_agent_name_matches_expected(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert result["agent"] == expected_agent_name

    def test_ticker_matches_input(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert result["ticker"] == "AAPL"

    def test_timestamp_is_nonempty_string(self, module, expected_agent_name, mocker, sample_key_figures):
        result = self._run(module, mocker, sample_key_figures)
        assert isinstance(result["timestamp"], str)
        assert len(result["timestamp"]) > 0

    def test_flags_with_red_flags_preserved(self, module, expected_agent_name, mocker, sample_key_figures):
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _submit_response(
            signal="bearish",
            score=2.0,
            flags=["HIGH_DEBT", "NEGATIVE_FCF"],
        )
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        result = module.analyze("AAPL", sample_key_figures)

        assert "HIGH_DEBT" in result["flags"]
        assert "NEGATIVE_FCF" in result["flags"]


# ── Fallback path — loop ends without submit_analysis ────────────────────────


class TestAgentFallback:
    """Tests the fallback return in run_agent when stop_reason == 'end_turn'."""

    def test_output_has_all_8_required_keys(self, mocker, sample_key_figures):
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _end_turn_response()
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        result = quality_agent.analyze("AAPL", sample_key_figures)

        assert set(result.keys()) == _REQUIRED_KEYS

    def test_fallback_signal_is_neutral(self, mocker, sample_key_figures):
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _end_turn_response()
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        result = quality_agent.analyze("AAPL", sample_key_figures)

        assert result["signal"] == "neutral"

    def test_fallback_score_is_5(self, mocker, sample_key_figures):
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _end_turn_response()
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        result = quality_agent.analyze("AAPL", sample_key_figures)

        assert result["score"] == 5.0

    def test_fallback_flags_contain_diagnostic_message(self, mocker, sample_key_figures):
        mock_client = mocker.MagicMock()
        mock_client.messages.create.return_value = _end_turn_response()
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        result = quality_agent.analyze("AAPL", sample_key_figures)

        assert any("submit_analysis" in flag for flag in result["flags"])
