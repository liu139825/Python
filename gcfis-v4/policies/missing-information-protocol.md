# GCFIS V4 Missing Information Protocol

## Principle

Missing information is never permission to guess. Every unresolved field must be recorded as `FOUND`, `PARTIAL`, `NOT_FOUND`, or `NOT_APPLICABLE` with observation time and attempted sources.

## Source hierarchy

1. **Live market and account data**: Alpaca and IBKR.
2. **Primary company and regulatory evidence**: SEC EDGAR, company investor relations, regulators, courts, exchanges, government statistical agencies.
3. **Current news and web facts**: Parallel Search, Reuters, official websites, Quartr, Financial Datasets and other verifiable sources.
4. **Academic evidence**: Sider Scholar, SciSpace and Scite.
5. **Educational background**: edX, used only for concepts, methods, market structure, quantitative finance and risk-management learning.

## Parallel Search fallback

Use Parallel Search when a current fact, catalyst, filing, event time, rule, public SSR record, official source link, or cross-source corroboration is missing.

- Run 2–3 targeted queries from different angles.
- Prioritize official and primary sources.
- Record publication time and observation time separately.
- Search snippets are evidence leads, not automatic truth; fetch the source when exact wording or details matter.
- Do not use Parallel Search as a substitute for live quotes, complete SIP volume, IBKR account data, real-time borrow inventory, or aggressor-side signed order flow.

## edX fallback

Use edX only when the missing item is educational or methodological, such as:

- market microstructure;
- electronic trading mechanics;
- liquidity and execution risk;
- statistics and probability calibration;
- quantitative finance and risk management.

Do not use edX for current news, live prices, earnings actuals, company filings, borrow availability, SSR status, event schedules, or intraday flow.

## Execution effect

- A **critical unresolved field** prevents a candidate from advancing to `READY`.
- A **non-critical unresolved field** may leave a candidate in `WATCH`, with reduced confidence and an explicit missing-data label.
- Real-time borrow availability must come from the broker or another authenticated lending source. Public short-interest data is delayed and cannot prove current borrow availability.
- SSR must be verified from official exchange/SEC data or marked unverified. A price-derived estimate may be shown only as an estimate.
- Absence of aggressor-side signed flow caps Flow Confidence and prohibits claims of institutional net inflow/outflow.

## Report section

Every PREMARKET, OPEN and CLOSE report must include a concise `Missing Data & Search Log` containing:

- missing field;
- sources attempted;
- result status;
- whether the gap affected candidate state or confidence;
- whether the field was later resolved without rewriting the earlier frozen snapshot.
