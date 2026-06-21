# Financial Data Visualization Builder

**What it does:** Creates 4–5 publication-quality financial charts that tell the story of a company's health across 3 years — balance sheet strength, profitability trends, cash generation quality, and capital efficiency.

**Best used in:** ChatGPT (with code interpreter)

## Prompt

DIRECTION: Create 4–5 visualisations that tell the story of [COMPANY NAME]'s financial health
over the past 3 years, answering key questions about balance sheet strength, profitability, and
cash generation.

PERSONA: You are an expert in financial data visualisation for institutional research. Your
strength is creating charts that are both rigorous and immediately understandable to portfolio
managers.

INPUT: Financial ratios for [COMPANY NAME] across 3 years (e.g. FY2023, FY2024, FY2025):
- Income statement: Revenue, EBITDA, Net profit
- Balance sheet: Total assets, Debt, Equity, Cash
- Cash flow: Operating cash flow, Capex, Free cash flow
- Key ratios: ROE, ROA, Debt-to-Equity, Current Ratio, Net Profit Margin, Interest Coverage
- Data format: [Python .csv / Excel .xlsx / provided below]

MEASURE — Create these visualisations:
Chart 1: Balance Sheet Strength Over Time (Line Chart) — Debt-to-Equity, Current Ratio, Cash
Ratio. Is the balance sheet stronger or weaker? Is leverage sustainable?
Chart 2: Profitability Trends (Combo Chart) — Bars: Revenue growth (YoY%), Line: Net Profit
Margin. Are profits in line with revenue? Margin compression?
Chart 3: Profitability vs Cash Generation (Dual-Axis Chart) — Left Y: Net Profit Margin (%),
Right Y: Operating Cash Flow (INR Cr). Are profits converting to cash?
Chart 4: Leverage & Debt Service Capacity (Bar/Line Combo) — Bars: Debt-to-Equity, Line: Interest
Coverage. Over-leveraged? Debt service capacity?
Chart 5 (Optional): Capital Efficiency — ROE and ROA trend over 3 years.

Platform: [Python matplotlib / Excel / Tableau / R ggplot2]
Colors: Professional palette, clear axis labels, legends, data sources.

Success criteria: A portfolio manager looking at 5 charts should quickly understand financial
health, key strengths, and weaknesses.
