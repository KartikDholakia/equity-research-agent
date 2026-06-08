"""yfinance client — EOD prices, technical indicators, and Indian fundamentals."""
from typing import Any

import pandas as pd
import yfinance as yf


def fetch_current_price(ticker: str) -> dict[str, Any]:
    """Return the latest price and basic market data for a ticker.

    Works for both US (AAPL) and Indian (.NS / .BO) tickers.
    Price and prev_close come from history() — more reliable than fast_info
    across markets. Market cap and 52-week range come from fast_info with
    safe fallbacks.
    """
    t = yf.Ticker(ticker)

    hist = t.history(period="5d")
    if hist.empty:
        raise ValueError(f"No price data for '{ticker}'. Check the ticker symbol.")

    price = round(float(hist["Close"].iloc[-1]), 4)
    prev_close = round(float(hist["Close"].iloc[-2]), 4) if len(hist) > 1 else None

    fi = t.fast_info
    return {
        "ticker": ticker,
        "price": price,
        "prev_close": prev_close,
        "currency": _safe_str(getattr(fi, "currency", None)),
        "market_cap": _safe_float(getattr(fi, "market_cap", None)),
        "fifty_two_week_high": _safe_float(getattr(fi, "year_high", None)),
        "fifty_two_week_low": _safe_float(getattr(fi, "year_low", None)),
    }


def fetch_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch OHLCV price history as a DataFrame.

    Args:
        ticker: e.g. "AAPL" or "ZOMATO.NS"
        period: yfinance period string — "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
        interval: bar size — "1d" (default), "1wk", "1mo"

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits.
        Index is DatetimeIndex in UTC. Empty DataFrame if ticker is invalid.
    """
    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No price data returned for '{ticker}'. Check the ticker symbol.")
    return df


def fetch_technical_indicators(ticker: str) -> dict[str, Any]:
    """Compute RSI-14, MACD, 200-DMA position, and volume trend from 1yr of daily data.

    Returns a flat dict with all indicator values and brief signal labels.
    Requires at least 200 trading days of history (a full calendar year is sufficient).
    """
    df = fetch_price_history(ticker, period="1y")
    close = df["Close"]

    rsi = _rsi(close)
    macd = _macd(close)
    dma = _dma200(close)
    volume = _volume_trend(df)

    return {
        "ticker": ticker,
        "rsi_14": rsi,
        "rsi_signal": _rsi_label(rsi),
        **macd,
        **dma,
        **volume,
    }


def fetch_fundamentals_yfinance(ticker: str) -> dict[str, Any]:
    """Fetch annual financial statements for any ticker supported by yfinance.

    Works for Indian (.NS / .BO), US, and other globally listed tickers.
    Returns DataFrames where columns = fiscal years (newest first) and rows = metrics.
    Raises ValueError if all DataFrames are empty (invalid or unsupported ticker).
    The info dict is returned as-is from yfinance — never raises, returns {} on failure.
    """
    t = yf.Ticker(ticker)

    income_stmt   = t.financials
    balance_sheet = t.balance_sheet
    cashflow      = t.cashflow

    if income_stmt.empty and balance_sheet.empty and cashflow.empty:
        raise ValueError(
            f"No fundamental data found for '{ticker}'. "
            "Verify the ticker includes the correct suffix (.NS for NSE, .BO for BSE)."
        )

    try:
        info = t.info or {}
    except Exception:
        info = {}

    return {
        "income_stmt":   income_stmt,
        "balance_sheet": balance_sheet,
        "cashflow":      cashflow,
        "info":          info,
    }


# ── Private helpers ────────────────────────────────────────────────────────────

def _safe_float(val: Any) -> float | None:
    """Return float or None — avoids crashes on NaN/None from fast_info."""
    try:
        f = float(val)
        return None if pd.isna(f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _safe_str(val: Any) -> str | None:
    """Return str or None."""
    return str(val) if val is not None else None


def _rsi(close: pd.Series, period: int = 14) -> float:
    """Wilder smoothed RSI using EWM (industry standard)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2)


def _rsi_label(rsi: float) -> str:
    if rsi >= 70:
        return "overbought"
    if rsi <= 30:
        return "oversold"
    return "neutral"


def _macd(close: pd.Series) -> dict[str, float]:
    """Standard MACD (12, 26, 9)."""
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": round(float(macd_line.iloc[-1]), 4),
        "macd_signal": round(float(signal_line.iloc[-1]), 4),
        "macd_histogram": round(float(histogram.iloc[-1]), 4),
        "macd_crossover": "bullish" if macd_line.iloc[-1] > signal_line.iloc[-1] else "bearish",
    }


def _dma200(close: pd.Series) -> dict[str, Any]:
    """200-day simple moving average position."""
    dma200 = close.rolling(window=200).mean().iloc[-1]
    current = close.iloc[-1]

    if pd.isna(dma200):
        return {"dma200": None, "pct_vs_dma200": None, "dma200_signal": "insufficient_data"}

    pct = round(((current - dma200) / dma200) * 100, 2)
    return {
        "dma200": round(float(dma200), 4),
        "pct_vs_dma200": pct,
        "dma200_signal": "above" if pct > 0 else "below",
    }


def _volume_trend(df: pd.DataFrame) -> dict[str, Any]:
    """Compare latest session volume against the 20-day average."""
    avg_20d = df["Volume"].tail(20).mean()
    latest = df["Volume"].iloc[-1]
    ratio = round(float(latest / avg_20d), 2) if avg_20d else None
    return {
        "volume_avg_20d": int(avg_20d) if avg_20d else None,
        "volume_latest": int(latest),
        "volume_ratio": ratio,
        "volume_signal": _volume_label(ratio),
    }


def _volume_label(ratio: float | None) -> str:
    if ratio is None:
        return "unknown"
    if ratio >= 1.5:
        return "high"
    if ratio <= 0.5:
        return "low"
    return "normal"
