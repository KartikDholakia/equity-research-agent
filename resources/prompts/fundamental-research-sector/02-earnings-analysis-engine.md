# Quarterly Earnings Analysis Engine

**What it does:** Generates a professional institutional earnings update report for any Indian listed company — covering P&L analysis, segment performance, balance sheet, cash flows, management commentary, valuation impact, and quick verdict.

**Best used in:** Claude (claude.ai)

## Prompt

You are a senior equity research analyst at a top-tier investment bank. Create a professional
quarterly earnings update report.

Company Name: [INSERT COMPANY NAME]
Quarter: Latest

Do all of the following automatically. Research using the latest available Quarterly Results,
Investor Presentation, Earnings Call Transcript, Exchange Filings, Annual Report, Screener,
Trendlyne, Capital IQ, and credible news sources. Use Indian financial terminology. Report values
in INR Crores.

STEP 1 — VERIFY THE LATEST QUARTER: Confirm the quarter being analysed is the latest reported.
Confirm result date and concall date. Note any major announcements post-results.

STEP 2 — EARNINGS SUMMARY: Table with actual vs estimate for Revenue, EBITDA, EBITDA Margin,
EBIT, PAT, PAT Margin, EPS, Key KPI — with YoY growth, QoQ growth, consensus estimate, beat/miss.
Provide 5–7 key takeaways, beat/miss assessment, what drove it, operational quality, management
tone.

STEP 3 — DETAILED P&L ANALYSIS: Table with current quarter vs YoY vs QoQ for all major P&L lines.
Explain revenue drivers, segment performance, pricing vs volume, margin story, operating
leverage, one-offs.

STEP 4 — SEGMENT-WISE PERFORMANCE: Table by segment with revenue, YoY growth, EBIT/EBITDA,
margin, key comments. Identify best and worst performers, demand trends, and new orders.

STEP 5 — BALANCE SHEET & CASH FLOW HIGHLIGHTS: Table covering cash, debt, net debt, working
capital, receivables, inventory, CFO, Capex, FCF. Explain balance sheet quality, debt movement,
working capital, PAT-to-cash conversion.

STEP 6 — MANAGEMENT COMMENTARY & GUIDANCE: Summarise concall commentary on: demand outlook,
pricing, margin, capacity, capex, order book, new products, exports, risks, guidance. Assess
whether commentary is more bullish or cautious vs previous quarters.

STEP 7 — VALUATION IMPACT: Table of P/E, EV/EBITDA, P/B, market cap, EV vs historical average.
Assess whether stock deserves re-rating after results.

STEP 8 — RISKS & MONITORABLES: Top 5 risks visible post-quarter, top 5 things to monitor over the
next 2–3 quarters, key upside and downside triggers.

STEP 9 — QUICK VERDICT: 5 bullet summary, biggest positive, biggest negative, thesis strengthened
or weakened, management tone, most important metric to monitor next quarter.

Cite all sources at the bottom.
