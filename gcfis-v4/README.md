# GCFIS V4

Structured research journal for event-conditioned, flow-confirmed intraday equity setups.

## Core principle
Keep PREMARKET, OPEN, and CLOSE evidence separate so post-close information never contaminates the original decision snapshot.

## Data discipline
- PREMARKET: catalyst, attention, gap, premarket flow/liquidity, theme/peer context, portfolio permission.
- OPEN: 09:30+ dollar volume, time-of-day RVOL, Opening VWAP/Range, price acceptance, relative strength, flow confidence, borrow/SSR, trigger/stop/target.
- CLOSE: high/low/close/VWAP, MFE/MAE, target-first vs stop-first, thesis validation, error classification and postmortem.
- `state=BACKFILL` is excluded from calibration analytics.

## Required environment variables
- `DATABASE_URL` — Neon Postgres connection string.
- `GCFIS_API_KEY` — private API write key.

## Local run
```bash
fastapi dev main.py
```

## FastAPI Cloud
The project is compatible with the FastAPI Cloud CLI:
```bash
fastapi deploy .
```
Set `DATABASE_URL` and `GCFIS_API_KEY` as secret environment variables in FastAPI Cloud before production use.

## Core endpoints
- `GET /health`
- `POST /api/v1/trading-days`
- `POST /api/v1/trading-days/{date}/candidates`
- `POST /api/v1/candidates/{id}/setup`
- `PUT /api/v1/candidates/{id}/outcome`
- `POST /api/v1/evidence`
- `GET /api/v1/days/{date}/close-summary`
- `GET /api/v1/analytics/setup-performance`
- `GET /api/v1/analytics/calibration`
