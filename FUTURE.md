# FUTURE.md — Enhancements Parking Lot

Ideas worth keeping but not assigned to any current phase.
Add entries here instead of cluttering PLAN.md with unscoped work.

---

## Frontend Revamp

The current Jinja2 + plain HTML/CSS frontend can be replaced entirely
without touching the backend. `web/app.py` calls `get_verdict_data()`
and passes a dict — the frontend is just a renderer.

**Drop-in options (keep FastAPI, change the renderer):**
- React / Vue / Svelte SPA — change `/research` to return JSON instead
  of HTML; frontend fetches and renders. FastAPI becomes a pure API.
- Tailwind CSS + shadcn/ui components — keep Jinja2, replace hand-rolled
  CSS with a proper design system. Low-effort, high visual quality jump.
- Use Claude artifacts to prototype a new layout first, then implement —
  faster than experimenting directly in the template.

**Bigger moves:**
- Next.js or SvelteKit as the full-stack JS layer — FastAPI stays as a
  Python-only backend behind an internal API boundary.
- Add charts: price + 200-DMA overlay (data already in
  `fetch_price_history()`) and a DCF bear/base/bull bar chart (data
  already in `value_agent` details). No new API needed — explicitly
  deprioritised in Phase 3 but the data is already there.

**When to revisit:** after Phase 5 (screener) or Phase 6 (portfolio),
once the tool has stabilised and the information density on the page is
clear. A revamp before content is settled is premature.

---

## Numbers with Threshold Context

Currently key figures are surfaced as raw numbers (e.g. "ROE: 24%").
A future pass should annotate each metric with its persona-specific
pass/fail interpretation:

- "ROE 24% → above Munger's 15% quality bar" ✓
- "PEG 0.8 → below Lynch's 1.0 threshold" ✓
- "D/E 1.52× → elevated for a non-financial firm" ⚠

Implementation: a threshold registry mapping each metric key to the
relevant agent's criteria + direction (above/below is good/bad).
This turns raw numbers into verifiable reasoning traces.
Already tracked as the last task in Phase 3 (PLAN.md).

---

## Public Deployment

Considered but explicitly deferred to Phase 9 (see PLAN.md). When ready:
- Deploy to Render or Fly.io
- Add a shared password gate (`INSTANCE_PASSWORD` env var)
- Pre-cache 3–5 analyses for a zero-live-API demo path
- Per-user accounts: separate decision at that point
