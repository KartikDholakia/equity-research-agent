# Mega Stock Research Framework

**What it does:** The most comprehensive stock analysis prompt in this library. Covers 12 parts — sector intelligence, financial forensics across 5 years, capital allocation, ratio dashboard, investor presentation analysis, concall forensics, annual report forensics, management integrity scoring, news/competitive analysis, community intelligence, growth trigger sizing, and a full bull/bear/base case final assessment.

**Best used in:** Claude (claude.ai)

## Prompt

Comprehensive Equity Research Framework | [COMPANY NAME] | [DATE]

PART 1 — SECTOR INTELLIGENCE
1.1 Sector Overview: Current trend (expansion/contraction/consolidation), key government
schemes/PLI incentives, regulatory changes in the last 12 months and their impact.
1.2 Trigger Map: Positive Triggers (macro, policy, demand-side catalysts) and Negative Triggers
(regulatory, cyclical, competitive, macro headwinds).

PART 2 — FINANCIAL FORENSICS (Last 5 Years)
2.1 P&L Deep Dive: Revenue acceleration or slowdown, margin trends with reasons, one-offs,
repetitive cost patterns, product mix analysis, margin mix analysis.
2.2 Balance Sheet Forensics: Asset quality, debt reduction or buildup, working capital
efficiency, contingent liabilities, goodwill, pledged promoter shares, off-balance-sheet items.
2.3 Cash Flow Forensics: CFO vs PAT conversion quality, divergences between profits and cash,
unusual investing or financing trends.

PART 3 — CAPITAL ALLOCATION ANALYSIS
3.1 Dividend History: Year-by-year dividend for last 5 years, payout ratio trend, special
dividends or cuts.
3.2 Capex Deep Dive: Total capex deployed (maintenance vs growth), current capex cycle status,
capacity expansion details, revenue impact modeling from new capacity.

PART 4 — RATIO DASHBOARD (Last 5 Years): Table with ROE, ROCE, Gross Block Growth, Asset
Turnover, Gross Block Turnover, D/E, Interest Coverage, Free Cash Flow, Total Assets, Inventory
Turnover, Reinvestment Ratio (Capex/CFO). For each ratio, state the 5-year trend and whether it
is improving or deteriorating. Call out top 3 positives and top 3 concerns.

PART 5 — INVESTOR PRESENTATION ANALYSIS (Last 12 Quarters): Promises vs Delivery Tracker, Product
Launch Pipeline, Revenue Segment Breakdown, Revenue Mix Trend, EBITDA Trend, Expansion Strategy,
Future Plans, Key Developments, Anything anomalous. Provide concise synthesis of most important
takeaways.

PART 6 — CONCALL FORENSICS (Last 12 Quarters): Growth commentary, new product lines, margin
guidance vs actual, headwinds/tailwinds, acquisition targets, backward integration, capex
progress, capacity utilisation trend, corporate actions, guidance track record table, any
material disclosures or management tone shifts.

PART 7 — ANNUAL REPORT FORENSICS: Red Flags (revenue recognition anomalies, related party
transactions, auditor qualifications or changes, loans to subsidiaries, receivables/inventory vs
revenue, standalone vs consolidated divergences). Hidden Positives (underreported segments, R&D
investments, operational improvements buried in notes, what numbers reveal that management hasn't
spoken about).

PART 8 — MANAGEMENT INTEGRITY SCORE: Matrix covering last 12 quarters: key promise made, whether
delivered, update given, red flags, green flags. Assign a composite Management Integrity Score out of 10 with reasoning covering delivery rate, transparency on misses, proactive disclosure,
analyst treatment, and tone consistency.

PART 9 — NEWS & COMPETITIVE LANDSCAPE: Recent news (last 90 days) on the company — material
developments only. Key competitor updates (market share shifts, new product launches, pricing
changes). Sector-level news with structural impact.

PART 10 — VALUEPICKR COMMUNITY INTELLIGENCE: Summarise key discussions, debates, and insights
from the ValuePickr thread for this company (last 90 days only). Flag high-conviction bullish or
bearish theses being discussed.

PART 11 — GROWTH TRIGGER ANALYSIS: Operating leverage (at what revenue level does margin
expansion kick in?), capex utilisation upside (revenue potential once current capex comes
online), acquisition revenue consolidation, key visible growth triggers (order book, client
additions, new geographies, regulatory/product approvals) with timelines.

PART 12 — FINAL ASSESSMENT:
Valuation Check: Current P/E vs 3-year and 5-year average, Price-to-Sales, Price-to-Book,
EV/EBITDA current vs historical range. State clearly whether stock appears overvalued, fairly
valued, or undervalued.
Overall Assessment: Bull Case (key assumptions, what needs to go right), Bear Case (key risks,
what could go wrong), Base Case (most likely outcome, return potential over 2–3 years).
Close with: single most important factor an investor should monitor for this company going
forward.
