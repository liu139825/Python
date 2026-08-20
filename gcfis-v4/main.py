from __future__ import annotations

import os
import secrets
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv("DATABASE_URL")
GCFIS_API_KEY = os.getenv("GCFIS_API_KEY")

app = FastAPI(
    title="GCFIS V4 Research Journal",
    version="0.1.0",
    description="Event-conditioned flow discovery, decision logging, and post-close calibration API.",
)


def get_conn():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def require_key(x_gcfis_key: str | None = Header(default=None)):
    if not GCFIS_API_KEY:
        raise HTTPException(status_code=503, detail="GCFIS_API_KEY is not configured")
    if not x_gcfis_key or not secrets.compare_digest(x_gcfis_key, GCFIS_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


class TradingDayIn(BaseModel):
    trade_date: date
    market_regime: str | None = None
    portfolio_permission: str | None = None
    account_nav: Decimal | None = None
    account_concentration_json: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class CandidateIn(BaseModel):
    symbol: str
    direction: Literal["LONG", "SHORT", "BOTH", "NONE"]
    catalyst_type: str | None = None
    catalyst_summary: str | None = None
    theme: str | None = None
    information_quality: str | None = None
    attention_type: str | None = None
    premarket_price: Decimal | None = None
    gap_pct: Decimal | None = None
    premarket_dollar_volume: Decimal | None = None
    premarket_rvol: Decimal | None = None
    opening_dollar_volume: Decimal | None = None
    opening_rvol: Decimal | None = None
    opening_vwap: Decimal | None = None
    price_at_decision: Decimal | None = None
    price_acceptance: str | None = None
    peer_confirmation: str | None = None
    relative_strength: Decimal | None = None
    flow_confidence: str | None = None
    crowding_risk: str | None = None
    borrow_status: str | None = None
    ssr: bool | None = None
    state: str | None = None
    decision_time: datetime | None = None
    rejected_reason: str | None = None


class SetupIn(BaseModel):
    trigger_price: Decimal | None = None
    stop_price: Decimal | None = None
    target_1: Decimal | None = None
    target_2: Decimal | None = None
    horizon_minutes: int | None = None
    expected_win_r: Decimal | None = None
    expected_loss_r: Decimal = Decimal("1")
    model_probability: Decimal | None = None
    probability_confidence: str | None = None
    expected_edge_r: Decimal | None = None
    live_permission: bool = False
    triggered: bool = False
    trigger_time: datetime | None = None


class OutcomeIn(BaseModel):
    close_price: Decimal | None = None
    day_high: Decimal | None = None
    day_low: Decimal | None = None
    session_vwap: Decimal | None = None
    mfe_r: Decimal | None = None
    mae_r: Decimal | None = None
    target_first: bool | None = None
    stopped_first: bool | None = None
    result_r: Decimal | None = None
    thesis_validated: bool | None = None
    closing_state: str | None = None
    postmortem: str | None = None


class EvidenceIn(BaseModel):
    candidate_id: int | None = None
    phase: Literal["PREMARKET", "OPEN", "CLOSE", "RESEARCH"]
    source_name: str
    source_type: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None
    observed_at: datetime | None = None
    fact: str
    data_freshness: str | None = None


@app.get("/health")
def health():
    db = False
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            db = cur.fetchone() is not None
    except Exception:
        db = False
    return {"ok": True, "database": db, "version": app.version}


@app.post("/api/v1/trading-days", dependencies=[Depends(require_key)])
def upsert_trading_day(payload: TradingDayIn):
    sql = """
    INSERT INTO trading_days(trade_date, market_regime, portfolio_permission, account_nav, account_concentration_json, notes)
    VALUES (%s,%s,%s,%s,%s,%s)
    ON CONFLICT (trade_date) DO UPDATE SET
      market_regime=EXCLUDED.market_regime,
      portfolio_permission=EXCLUDED.portfolio_permission,
      account_nav=EXCLUDED.account_nav,
      account_concentration_json=EXCLUDED.account_concentration_json,
      notes=EXCLUDED.notes
    RETURNING *
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (payload.trade_date, payload.market_regime, payload.portfolio_permission,
                          payload.account_nav, psycopg.types.json.Jsonb(payload.account_concentration_json), payload.notes))
        row = cur.fetchone(); conn.commit(); return row


@app.post("/api/v1/trading-days/{trade_date}/candidates", dependencies=[Depends(require_key)])
def upsert_candidate(trade_date: date, payload: CandidateIn):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM trading_days WHERE trade_date=%s", (trade_date,))
        d = cur.fetchone()
        if not d:
            raise HTTPException(404, "Trading day not found")
        cols = list(payload.model_dump().keys())
        vals = list(payload.model_dump().values())
        insert_cols = ",".join(["trading_day_id"] + cols)
        placeholders = ",".join(["%s"] * (len(vals) + 1))
        updates = ",".join([f"{c}=EXCLUDED.{c}" for c in cols if c != "symbol"])
        sql = f"INSERT INTO candidates({insert_cols}) VALUES ({placeholders}) ON CONFLICT(trading_day_id,symbol) DO UPDATE SET {updates} RETURNING *"
        cur.execute(sql, [d["id"], *vals]); row = cur.fetchone(); conn.commit(); return row


@app.post("/api/v1/candidates/{candidate_id}/setup", dependencies=[Depends(require_key)])
def add_setup(candidate_id: int, payload: SetupIn):
    data = payload.model_dump()
    cols = list(data.keys())
    sql = f"INSERT INTO trade_setups(candidate_id,{','.join(cols)}) VALUES ({','.join(['%s']*(len(cols)+1))}) RETURNING *"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, [candidate_id, *data.values()]); row = cur.fetchone(); conn.commit(); return row


@app.put("/api/v1/candidates/{candidate_id}/outcome", dependencies=[Depends(require_key)])
def upsert_outcome(candidate_id: int, payload: OutcomeIn):
    data = payload.model_dump(); cols = list(data.keys())
    updates = ",".join([f"{c}=EXCLUDED.{c}" for c in cols])
    sql = f"INSERT INTO outcomes(candidate_id,{','.join(cols)}) VALUES ({','.join(['%s']*(len(cols)+1))}) ON CONFLICT(candidate_id) DO UPDATE SET {updates}, captured_at=now() RETURNING *"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, [candidate_id, *data.values()]); row = cur.fetchone(); conn.commit(); return row


@app.post("/api/v1/evidence", dependencies=[Depends(require_key)])
def add_evidence(payload: EvidenceIn):
    data = payload.model_dump()
    if data["observed_at"] is None:
        data["observed_at"] = datetime.now().astimezone()
    cols = list(data.keys())
    sql = f"INSERT INTO evidence({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))}) RETURNING *"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, list(data.values())); row = cur.fetchone(); conn.commit(); return row


@app.get("/api/v1/days/{trade_date}/close-summary")
def close_summary(trade_date: date):
    sql = """
    SELECT c.*, s.trigger_price, s.stop_price, s.target_1, s.target_2,
           s.expected_win_r, s.expected_loss_r, s.model_probability, s.probability_confidence,
           s.expected_edge_r, s.live_permission, s.triggered,
           o.close_price, o.day_high, o.day_low, o.session_vwap, o.mfe_r, o.mae_r,
           o.target_first, o.stopped_first, o.result_r, o.thesis_validated, o.closing_state, o.postmortem
    FROM trading_days d
    JOIN candidates c ON c.trading_day_id=d.id
    LEFT JOIN LATERAL (SELECT * FROM trade_setups x WHERE x.candidate_id=c.id ORDER BY x.created_at DESC LIMIT 1) s ON true
    LEFT JOIN outcomes o ON o.candidate_id=c.id
    WHERE d.trade_date=%s
    ORDER BY COALESCE(s.expected_edge_r,-999) DESC, c.opening_rvol DESC NULLS LAST
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM trading_days WHERE trade_date=%s", (trade_date,)); day = cur.fetchone()
        if not day: raise HTTPException(404, "Trading day not found")
        cur.execute(sql, (trade_date,)); candidates = cur.fetchall()
        return {"day": day, "candidates": candidates}


@app.get("/api/v1/analytics/setup-performance")
def setup_performance(min_samples: int = Query(5, ge=1)):
    sql = """
    SELECT COALESCE(c.catalyst_type,'UNKNOWN') catalyst_type, c.direction,
           COUNT(*) samples,
           AVG(CASE WHEN o.thesis_validated THEN 1.0 ELSE 0.0 END) validation_rate,
           AVG(o.result_r) avg_result_r,
           AVG(o.mfe_r) avg_mfe_r,
           AVG(o.mae_r) avg_mae_r
    FROM candidates c JOIN outcomes o ON o.candidate_id=c.id
    WHERE COALESCE(c.state,'') <> 'BACKFILL'
    GROUP BY 1,2 HAVING COUNT(*) >= %s ORDER BY avg_result_r DESC NULLS LAST
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (min_samples,)); return cur.fetchall()


@app.get("/api/v1/analytics/calibration")
def calibration():
    sql = """
    SELECT CASE
      WHEN s.model_probability IS NULL THEN 'unscored'
      WHEN s.model_probability < .55 THEN '<55%'
      WHEN s.model_probability < .65 THEN '55-65%'
      WHEN s.model_probability < .75 THEN '65-75%'
      ELSE '75%+'
    END bucket,
    COUNT(*) samples,
    AVG(CASE WHEN o.target_first THEN 1.0 ELSE 0.0 END) realized_target_first_rate,
    AVG(o.result_r) avg_result_r
    FROM trade_setups s JOIN outcomes o ON o.candidate_id=s.candidate_id
    JOIN candidates c ON c.id=s.candidate_id
    WHERE COALESCE(c.state,'') <> 'BACKFILL'
    GROUP BY 1 ORDER BY 1
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql); return cur.fetchall()
