"""CLI entry point for the equity research agent."""
import argparse
import sys
from typing import Literal
from agents.orchestrator import run_analysis

QueryType = Literal["analyze", "screen", "review", "allocate"]


def detect_market(ticker: str) -> str:
    """Infer market from ticker suffix (.NS / .BO → india, else us)."""
    if ticker.upper().endswith(".NS") or ticker.upper().endswith(".BO"):
        return "india"
    return "us"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="equity-research-agent",
        description="Personal AI-powered equity research tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python main.py --ticker AAPL
  python main.py --ticker ZOMATO.NS
  python main.py --screen india
  python main.py --review
  python main.py --allocate 50000
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ticker",
        type=str,
        metavar="TICKER",
        help="Analyze a stock (e.g. AAPL, ZOMATO.NS)",
    )
    group.add_argument(
        "--screen",
        choices=["india", "us"],
        metavar="MARKET",
        help="Run monthly screener for a market (india | us)",
    )
    group.add_argument(
        "--review",
        action="store_true",
        help="Run a portfolio review across all holdings",
    )
    group.add_argument(
        "--allocate",
        type=float,
        metavar="AMOUNT",
        help="Find the best use for a cash amount (e.g. 50000)",
    )

    parser.add_argument(
        "--market",
        choices=["us", "india"],
        help="Override auto-detected market (only used with --ticker)",
    )

    return parser


def route(args: argparse.Namespace) -> tuple[QueryType, dict]:
    """Map parsed args to a query type and a context dict."""
    if args.ticker:
        market = args.market or detect_market(args.ticker)
        return "analyze", {"ticker": args.ticker.upper(), "market": market}

    if args.screen:
        return "screen", {"market": args.screen}

    if args.review:
        return "review", {}

    # args.allocate
    return "allocate", {"amount": args.allocate}


def run_analyze(ticker: str, market: str) -> None:
    """Delegate to the orchestrator for single-stock analysis."""
    # TODO: Add try catch block
    run_analysis(ticker=ticker, market=market)


def run_screen(market: str) -> None:
    """Surface top screener candidates. Available in Phase 3."""
    print(f"[Phase 3] Screener for {market.upper()} market — not yet implemented.")


def run_review() -> None:
    """Run a portfolio review across all holdings. Available in Phase 5."""
    print("[Phase 5] Portfolio review — not yet implemented.")


def run_allocate(amount: float) -> None:
    """Rank candidates and suggest ₹/$ allocation. Available in Phase 5."""
    print(f"[Phase 5] Allocation query for {amount:,.0f} — not yet implemented.")


def main() -> None:
    """Parse args, route to the right workflow, and run it."""
    parser = build_parser()
    args = parser.parse_args()
    query_type, context = route(args)

    handlers = {
        "analyze": lambda: run_analyze(**context),
        "screen": lambda: run_screen(**context),
        "review": run_review,
        "allocate": lambda: run_allocate(**context),
    }
    handlers[query_type]()


if __name__ == "__main__":
    main()
