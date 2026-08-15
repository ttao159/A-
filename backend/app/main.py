"""FastAPI 入口与 REST 路由。"""

import json
import queue
import threading
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import backtest, config
from .account import AccountService
from .database import Base, SessionLocal, engine, get_db, migrate
from .generator import run_generation
from .market import MarketDataService
from .models import Backtest, EquityPoint, GenerationReport, ScanReport, Strategy
from .public_data import DataUnavailableError
from .scanner import scan_and_trade
from .schemas import BacktestRequest, GeneratorRequest, StrategyCreate, StrategyUpdate
from .scheduler import start_scheduler

Base.metadata.create_all(bind=engine)
migrate()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(title="A股自动交易助手", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

market = MarketDataService()
accounts = AccountService()


def _strategy_out(s: Strategy) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "enabled": bool(s.enabled),
        "config": json.loads(s.config_json),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


# ===== 策略 =====
@app.get("/api/strategies")
def list_strategies(db: Session = Depends(get_db)):
    return [_strategy_out(s) for s in db.query(Strategy).all()]


@app.post("/api/strategies")
def create_strategy(body: StrategyCreate, db: Session = Depends(get_db)):
    s = Strategy(name=body.name, enabled=int(body.enabled),
                 config_json=json.dumps(body.config, ensure_ascii=False))
    db.add(s)
    db.commit()
    db.refresh(s)
    return _strategy_out(s)


@app.put("/api/strategies/{sid}")
def update_strategy(sid: int, body: StrategyUpdate, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == sid).first()
    if not s:
        raise HTTPException(404, "策略不存在")
    if body.name is not None:
        s.name = body.name
    if body.enabled is not None:
        s.enabled = int(body.enabled)
    if body.config is not None:
        s.config_json = json.dumps(body.config, ensure_ascii=False)
    db.commit()
    db.refresh(s)
    return _strategy_out(s)


@app.delete("/api/strategies/{sid}")
def delete_strategy(sid: int, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == sid).first()
    if not s:
        raise HTTPException(404, "策略不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}


# ===== 回测 =====
@app.post("/api/strategies/{sid}/backtest")
def run_strategy_backtest(sid: int, body: BacktestRequest, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == sid).first()
    if not s:
        raise HTTPException(404, "策略不存在")

    today = date.today()
    end = body.end_date or today.isoformat()
    start = body.start_date or (today - timedelta(days=365)).isoformat()

    cfg = json.loads(s.config_json)
    result = backtest.run_backtest(cfg, market, start, end)

    bt = Backtest(strategy_id=s.id, start_date=start, end_date=end,
                  metrics_json=json.dumps(result["metrics"], ensure_ascii=False))
    db.add(bt)
    db.flush()
    for p in result["equity_curve"]:
        db.add(EquityPoint(backtest_id=bt.id, date=p["date"], equity=p["equity"]))
    db.commit()
    db.refresh(bt)

    return {
        "id": bt.id,
        "strategy_id": s.id,
        "start_date": start,
        "end_date": end,
        "metrics": result["metrics"],
        "equity_curve": result["equity_curve"],
        "trades": result["trades"],
        "signal_stats": result["signal_stats"],
    }


@app.get("/api/strategies/{sid}/backtests")
def list_backtests(sid: int, db: Session = Depends(get_db)):
    items = (db.query(Backtest)
             .filter(Backtest.strategy_id == sid)
             .order_by(Backtest.id.desc())
             .limit(20).all())
    return [{
        "id": bt.id,
        "strategy_id": bt.strategy_id,
        "start_date": bt.start_date,
        "end_date": bt.end_date,
        "metrics": json.loads(bt.metrics_json or "{}"),
        "created_at": bt.created_at.isoformat() if bt.created_at else None,
    } for bt in items]


@app.get("/api/strategies/{sid}/backtests/{bid}")
def get_backtest(sid: int, bid: int, db: Session = Depends(get_db)):
    bt = db.query(Backtest).filter(Backtest.id == bid, Backtest.strategy_id == sid).first()
    if not bt:
        raise HTTPException(404, "回测不存在")
    curve = db.query(EquityPoint).filter(EquityPoint.backtest_id == bt.id).order_by(EquityPoint.id).all()
    return {
        "id": bt.id,
        "strategy_id": bt.strategy_id,
        "start_date": bt.start_date,
        "end_date": bt.end_date,
        "metrics": json.loads(bt.metrics_json or "{}"),
        "equity_curve": [{"date": p.date, "equity": p.equity} for p in curve],
    }


# ===== 策略生成引擎 =====
@app.post("/api/generator/run")
def run_strategy_generator(body: GeneratorRequest, db: Session = Depends(get_db)):
    """启发式生成策略 + 公开 API 真实行情回测 + 多策略对比报告，并落库历史。"""
    try:
        report = run_generation(body.model_dump(), market)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))

    g = GenerationReport(
        request_json=json.dumps(body.model_dump(), ensure_ascii=False),
        report_json=json.dumps(report, ensure_ascii=False),
        recommended_index=report.get("recommended_index", 0) or 0,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    report["id"] = g.id
    return report


@app.post("/api/generator/run/stream")
def run_strategy_generator_stream(body: GeneratorRequest):
    """流式生成策略：NDJSON 逐行输出进度事件，末行输出完整报告。"""
    q = queue.Queue()

    def progress(stage, message, done, total):
        q.put({"type": "progress", "stage": stage, "message": message,
               "done": done, "total": total})

    def worker():
        try:
            report = run_generation(body.model_dump(), market, progress=progress)
            q.put({"type": "result", "report": report})
        except ValueError as exc:
            q.put({"type": "error", "detail": str(exc), "status": 400})
        except DataUnavailableError as exc:
            q.put({"type": "error", "detail": str(exc), "status": 502})
        except Exception as exc:
            q.put({"type": "error", "detail": str(exc), "status": 500})

    threading.Thread(target=worker, daemon=True).start()

    def gen():
        while True:
            evt = q.get()
            if evt["type"] == "error":
                yield json.dumps(evt, ensure_ascii=False) + "\n"
                break
            if evt["type"] == "result":
                report = evt["report"]
                db = SessionLocal()
                try:
                    g = GenerationReport(
                        request_json=json.dumps(body.model_dump(), ensure_ascii=False),
                        report_json=json.dumps(report, ensure_ascii=False),
                        recommended_index=report.get("recommended_index", 0) or 0,
                    )
                    db.add(g)
                    db.commit()
                    db.refresh(g)
                    report["id"] = g.id
                finally:
                    db.close()
                yield json.dumps({"type": "result", "report": report}, ensure_ascii=False) + "\n"
                break
            yield json.dumps(evt, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.get("/api/generator/reports")
def list_generation_reports(db: Session = Depends(get_db)):
    """查询策略生成历史（最近 20 条，不含完整报告）。"""
    items = db.query(GenerationReport).order_by(GenerationReport.id.desc()).limit(20).all()
    return [{
        "id": g.id,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "recommended_index": g.recommended_index,
        "request": json.loads(g.request_json or "{}"),
    } for g in items]


@app.get("/api/generator/reports/{gid}")
def get_generation_report(gid: int, db: Session = Depends(get_db)):
    """查询某次策略生成的完整报告。"""
    g = db.query(GenerationReport).filter(GenerationReport.id == gid).first()
    if not g:
        raise HTTPException(404, "生成报告不存在")
    return json.loads(g.report_json or "{}")


# ===== 账户 =====
@app.get("/api/account")
def get_account(db: Session = Depends(get_db)):
    acct, positions, _ = accounts.get_snapshot(db)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()
    market_value = 0.0
    for p in positions:
        price = p.avg_cost
        try:
            bars = market.get_daily_bars(p.code, start, end)
            if bars is not None and len(bars):
                price = float(bars["close"].iloc[-1])
        except Exception:
            pass
        market_value += p.qty * price
    total = acct.available_cash + market_value
    return {
        "initial_capital": acct.initial_capital,
        "available_cash": round(acct.available_cash, 2),
        "market_value": round(market_value, 2),
        "total_asset": round(total, 2),
        "total_pnl": round(total - acct.initial_capital, 2),
    }


@app.get("/api/positions")
def get_positions(db: Session = Depends(get_db)):
    _, positions, _ = accounts.get_snapshot(db)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()
    result = []
    for p in positions:
        price = p.avg_cost
        try:
            bars = market.get_daily_bars(p.code, start, end)
            if bars is not None and len(bars):
                price = float(bars["close"].iloc[-1])
        except Exception:
            pass
        pnl_pct = (price - p.avg_cost) / p.avg_cost * 100.0 if p.avg_cost else 0.0
        result.append({
            "code": p.code, "name": p.name, "qty": p.qty,
            "avg_cost": round(p.avg_cost, 3), "price": round(price, 3),
            "pnl_pct": round(pnl_pct, 2),
            "pnl": round((price - p.avg_cost) * p.qty, 2),
            "hold_days": p.hold_days or 0,
        })
    return result


@app.get("/api/trades")
def get_trades(db: Session = Depends(get_db)):
    _, _, trades = accounts.get_snapshot(db)
    return [
        {
            "id": t.id, "code": t.code, "name": t.name, "direction": t.direction,
            "qty": t.qty, "price": t.price, "commission": round(t.commission, 2),
            "tax": round(t.tax, 2), "pnl": round(t.pnl, 2),
            "traded_at": t.traded_at.isoformat() if t.traded_at else None,
        }
        for t in trades
    ]


@app.get("/api/stocks")
def get_stocks():
    return [{"code": c, "name": n} for c, n in market.get_stock_list()]


@app.get("/api/stocks/{code}/bars")
def get_stock_bars(code: str, days: int = 90, period: str = "day", adjust: str = "qfq"):
    period = (period or "day").lower()
    adjust = (adjust or "qfq").lower()
    day_span = {"day": 1, "week": 7, "month": 31, "year": 366}.get(period, 1)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days * day_span + 30)).isoformat()
    try:
        if period == "day":
            df = market.get_daily_bars(code, start, end, adjust)
        else:
            df = market.get_kline(code, period, start, end, adjust)
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))
    if df is None or len(df) == 0:
        raise HTTPException(404, "无行情数据")
    df = df.tail(days)
    return [
        {"date": r["date"], "open": round(float(r["open"]), 3),
         "high": round(float(r["high"]), 3), "low": round(float(r["low"]), 3),
         "close": round(float(r["close"]), 3), "volume": float(r["volume"])}
        for _, r in df.iterrows()
    ]


@app.get("/api/stocks/{code}/minute")
def get_stock_minute(code: str):
    """返回当日分时数据（价格/成交量，含昨收价）。"""
    try:
        return market.get_minute_bars(code)
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))


@app.post("/api/scan")
def trigger_scan(db: Session = Depends(get_db)):
    """手动触发一次全市场扫描交易。"""
    report = scan_and_trade(db, market, accounts)
    return report


@app.get("/api/scan/reports")
def list_scan_reports(db: Session = Depends(get_db)):
    """查询扫描历史报告（最近 20 条）。"""
    items = db.query(ScanReport).order_by(ScanReport.id.desc()).limit(20).all()
    return [{
        "id": r.id,
        "strategy_count": r.strategy_count,
        "buy_count": r.buy_count,
        "sell_count": r.sell_count,
        "reject_count": r.reject_count,
        "source": r.source or "manual",
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in items]


@app.post("/api/account/reset")
def reset_account(db: Session = Depends(get_db)):
    """重置模拟账户：清空持仓、订单与成交，资金恢复初始值。"""
    from .models import Order, Position, Trade

    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    db.query(Position).filter(Position.account_id == acct.id).delete()
    db.query(Trade).filter(Trade.account_id == acct.id).delete()
    db.query(Order).filter(Order.account_id == acct.id).delete()
    acct.available_cash = acct.initial_capital
    db.commit()
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="/workspace", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
