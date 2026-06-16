# Equity Research Agent

A personal AI-powered equity research tool. Analyzes Indian (NSE/BSE) and
US stocks, tracks a portfolio, and surfaces investment decisions. The
human always makes the final call — this is a decision-support tool, not
a trading bot.

See `SPEC.md` for the full product spec and `ARCHITECTURE.md` for system
design.

## Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (used to manage the virtual
  environment for this project)

```bash
pip install uv
```

## Setup

1. Create the virtual environment (run from the project root):

   ```bash
   uv venv .venv
   ```

2. Activate it:

   ```bash
   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   uv pip install -r requirements.txt
   ```

   > Use `uv pip install` (not plain `pip install`) so packages land in
   > this project's `.venv`.

4. Set up environment variables — create a `.env` file in the project
   root with the following keys (see `CLAUDE.md` for the full list):

   ```
   ANTHROPIC_API_KEY=
   FMP_API_KEY=
   ALPHA_VANTAGE_API_KEY=
   GOOGLE_SHEETS_CREDS_PATH=credentials.json
   PORTFOLIO_SHEET_ID=
   ```

## Usage

```bash
# Analyze a stock
python main.py --ticker AAPL
python main.py --ticker ZOMATO.NS

# Run a screener
python main.py --screen india

# Portfolio review
python main.py --review

# Run the dashboard
streamlit run dashboard/app.py
```

## Running Tests

```bash
pytest
```

## Project Structure

See the "Project Structure" section in `CLAUDE.md` for the target
directory layout (`agents/`, `data/`, `tools/`, `dashboard/`, `digest/`,
`tests/`).

---

*This README is a basic draft — to be refined as the project matures.*
