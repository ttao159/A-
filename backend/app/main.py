"""FastAPI 入口与 REST 路由。"""

import json
import queue
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import backtest, config, optimizer
from .account import AccountService
from .broker import get_broker
from .database import Base, SessionLocal, engine, get_db, migrate
from .generator import run_generation
from .industry_map import industry_map
from .market import MarketDataService
from .models import Alert, Backtest, EquityPoint, GenerationReport, Order, ScanReport, Strategy, Trade
from .public_data import DataUnavailableError
from .scanner import scan_and_trade, scan_lock
from .schemas import BacktestRequest, GeneratorRequest, OptimizeRequest, OrderPrepareRequest, StrategyCreate, StrategyUpdate
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
        "initial_capital": round(s.initial_capital or 0.0, 2),
        "available_cash": round(s.available_cash or 0.0, 2),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


# ===== 策略 =====
@app.get("/api/strategies")
def list_strategies(db: Session = Depends(get_db)):
    return [_strategy_out(s) for s in db.query(Strategy).all()]


@app.get("/api/strategies/compare")
def compare_strategies(db: Session = Depends(get_db)):
    """多策略收益对比：每个策略的总资产、盈亏与收益率，按收益率降序。"""
    strategies = db.query(Strategy).all()
    _, positions, _ = accounts.get_snapshot(db)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()

    pos_by_strategy = {}
    for p in positions:
        if p.strategy_id is not None:
            pos_by_strategy.setdefault(p.strategy_id, []).append(p)

    result = []
    for s in strategies:
        capital = s.initial_capital or 0.0
        cash = s.available_cash or 0.0
        market_value = 0.0
        for p in pos_by_strategy.get(s.id, []):
            price = p.avg_cost
            try:
                bars = market.get_daily_bars(p.code, start, end)
                if bars is not None and len(bars):
                    price = float(bars["close"].iloc[-1])
            except Exception:
                pass
            market_value += p.qty * price
        total = cash + market_value
        pnl = total - capital
        ret_pct = (pnl / capital * 100.0) if capital else 0.0
        result.append({
            "id": s.id,
            "name": s.name,
            "enabled": bool(s.enabled),
            "initial_capital": round(capital, 2),
            "available_cash": round(cash, 2),
            "market_value": round(market_value, 2),
            "total_asset": round(total, 2),
            "pnl": round(pnl, 2),
            "return_pct": round(ret_pct, 2),
        })
    result.sort(key=lambda x: x["return_pct"], reverse=True)
    return result


@app.post("/api/strategies")
def create_strategy(body: StrategyCreate, db: Session = Depends(get_db)):
    capital = body.initial_capital if body.initial_capital is not None else config.DEFAULT_INITIAL_CAPITAL
    s = Strategy(name=body.name, enabled=int(body.enabled),
                 config_json=json.dumps(body.config, ensure_ascii=False),
                 initial_capital=capital, available_cash=capital)
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
    if body.initial_capital is not None:
        invested = 0.0
        for p in db.query(Position).filter(Position.strategy_id == s.id).all():
            invested += p.avg_cost * p.qty
        if body.initial_capital < invested:
            raise HTTPException(400, "分配金额不能低于当前持仓成本")
        s.initial_capital = body.initial_capital
        s.available_cash = body.initial_capital - invested
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


@app.delete("/api/strategies/{sid}/backtests/{bid}")
def delete_backtest(sid: int, bid: int, db: Session = Depends(get_db)):
    bt = db.query(Backtest).filter(Backtest.id == bid, Backtest.strategy_id == sid).first()
    if not bt:
        raise HTTPException(404, "回测不存在")
    db.query(EquityPoint).filter(EquityPoint.backtest_id == bt.id).delete()
    db.delete(bt)
    db.commit()
    return {"status": "deleted"}


# ===== 参数优化 =====
@app.post("/api/strategies/{sid}/optimize")
def optimize_strategy(sid: int, body: OptimizeRequest, db: Session = Depends(get_db)):
    """对策略参数网格搜索，返回按历史回测总收益降序的最优组合。"""
    s = db.query(Strategy).filter(Strategy.id == sid).first()
    if not s:
        raise HTTPException(404, "策略不存在")
    today = date.today()
    end = body.end_date or today.isoformat()
    start = body.start_date or (today - timedelta(days=365)).isoformat()
    cfg = json.loads(s.config_json)
    capital = s.initial_capital or config.DEFAULT_INITIAL_CAPITAL
    try:
        results, sample_info = optimizer.optimize(cfg, market, start, end, body.param_grid,
                                                  initial_capital=capital,
                                                  stock_limit=body.stock_limit)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))
    return {"strategy_id": s.id, "start_date": start, "end_date": end,
            "sample": sample_info, "results": results}


@app.post("/api/strategies/{sid}/optimize/stream")
def optimize_strategy_stream(sid: int, body: OptimizeRequest):
    """流式参数优化：NDJSON 逐行输出进度，末行输出完整优化结果。"""
    db = SessionLocal()
    try:
        s = db.query(Strategy).filter(Strategy.id == sid).first()
        if not s:
            raise HTTPException(404, "策略不存在")
        today = date.today()
        end = body.end_date or today.isoformat()
        start = body.start_date or (today - timedelta(days=365)).isoformat()
        cfg = json.loads(s.config_json)
        capital = s.initial_capital or config.DEFAULT_INITIAL_CAPITAL
    finally:
        db.close()

    q = queue.Queue()

    def progress(stage, message, done, total):
        q.put({"type": "progress", "stage": stage, "message": message,
               "done": done, "total": total})

    def worker():
        try:
            results, sample_info = optimizer.optimize(cfg, market, start, end, body.param_grid,
                                                      initial_capital=capital,
                                                      stock_limit=body.stock_limit,
                                                      progress=progress)
            q.put({"type": "result", "results": results, "sample": sample_info})
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
                yield json.dumps(evt, ensure_ascii=False) + "\n"
                break
            yield json.dumps(evt, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


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


@app.delete("/api/generator/reports/{gid}")
def delete_generation_report(gid: int, db: Session = Depends(get_db)):
    """删除某次策略生成报告。"""
    g = db.query(GenerationReport).filter(GenerationReport.id == gid).first()
    if not g:
        raise HTTPException(404, "生成报告不存在")
    db.delete(g)
    db.commit()
    return {"status": "deleted"}


# ===== 账户 =====
@app.get("/api/account")
def get_account(db: Session = Depends(get_db)):
    acct, positions, _ = accounts.get_snapshot(db)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()
    quotes = market.get_realtime_quotes([p.code for p in positions]) if positions else {}
    market_value = 0.0
    for p in positions:
        price = p.avg_cost
        rt = quotes.get(p.code)
        if rt:
            price = rt["price"]
        else:
            try:
                bars = market.get_daily_bars(p.code, start, end)
                if bars is not None and len(bars):
                    price = float(bars["close"].iloc[-1])
            except Exception:
                pass
        market_value += p.qty * price
    strategies = db.query(Strategy).all()
    cash = sum(s.available_cash or 0.0 for s in strategies)
    capital = sum(s.initial_capital or 0.0 for s in strategies)
    total = cash + market_value
    accounts.record_equity(db, acct, total)
    curve = accounts.equity_curve(db, acct, limit=2)
    today_pnl = 0.0
    if len(curve) >= 2 and curve[-1]["date"] == date.today().isoformat():
        today_pnl = round(curve[-1]["equity"] - curve[-2]["equity"], 2)
    return {
        "broker_type": config.BROKER_TYPE,
        "initial_capital": round(capital, 2),
        "available_cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "total_asset": round(total, 2),
        "total_pnl": round(total - capital, 2),
        "today_pnl": today_pnl,
    }


@app.get("/api/account/equity")
def get_account_equity(db: Session = Depends(get_db)):
    """账户历史总资产曲线（最近 60 个交易日）。"""
    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    return accounts.equity_curve(db, acct, limit=60)


@app.post("/api/account/diagnose")
def diagnose_account(db: Session = Depends(get_db)):
    """AI 账户健康度诊断：基于账户快照调用智能体，未配置 LLM 时启发式降级。"""
    from .agents import account_diagnosis

    acct, positions, _ = accounts.get_snapshot(db)
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()
    quotes = market.get_realtime_quotes([p.code for p in positions]) if positions else {}
    market_value = 0.0
    pos_list = []
    for p in positions:
        price = p.avg_cost
        rt = quotes.get(p.code)
        if rt:
            price = rt["price"]
        else:
            try:
                bars = market.get_daily_bars(p.code, start, end)
                if bars is not None and len(bars):
                    price = float(bars["close"].iloc[-1])
            except Exception:
                pass
        mv = p.qty * price
        market_value += mv
        pnl_pct = (price - p.avg_cost) / p.avg_cost * 100.0 if p.avg_cost else 0.0
        pos_list.append({
            "code": p.code, "name": p.name, "qty": p.qty,
            "avg_cost": round(p.avg_cost, 3), "price": round(price, 3),
            "pnl": round((price - p.avg_cost) * p.qty, 2),
            "pnl_pct": round(pnl_pct, 2),
        })
    strategies = db.query(Strategy).all()
    cash = sum(s.available_cash or 0.0 for s in strategies)
    capital = sum(s.initial_capital or 0.0 for s in strategies)
    total = cash + market_value
    accounts.record_equity(db, acct, total)
    curve = accounts.equity_curve(db, acct, limit=30)

    for p in pos_list:
        p["weight"] = round(p["qty"] * p["price"] / total, 4) if total else 0

    sells = [t for t in db.query(Trade).filter(
        Trade.account_id == acct.id, Trade.direction == "sell").all() if t.pnl is not None]
    wins = sum(1 for t in sells if t.pnl > 0)
    win_rate = wins / len(sells) if sells else None
    alert_count = db.query(Alert).filter(Alert.account_id == acct.id).count()

    today_pnl = 0.0
    if len(curve) >= 2 and curve[-1]["date"] == date.today().isoformat():
        today_pnl = round(curve[-1]["equity"] - curve[-2]["equity"], 2)

    ctx = {
        "broker_type": config.BROKER_TYPE,
        "total_asset": round(total, 2),
        "initial_capital": round(capital, 2),
        "total_pnl": round(total - capital, 2),
        "today_pnl": today_pnl,
        "available_cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "position_count": len(pos_list),
        "strategy_count": len(strategies),
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "closed_pnl": round(sum(t.pnl for t in sells), 2),
        "alert_count": alert_count,
        "equity_curve": curve,
        "positions": pos_list,
    }
    return account_diagnosis(ctx)


@app.get("/api/account/daily-pnl")
def get_account_daily_pnl(db: Session = Depends(get_db)):
    """账户每日盈亏（最近 120 个记录日），供收益日历展示。"""
    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    return accounts.daily_pnl(db, acct, limit=120)


@app.get("/api/account/pnl-attribution")
def get_pnl_attribution(db: Session = Depends(get_db)):
    """今日盈亏归因：按持仓当日涨跌贡献聚合（优先板块，行业映射未就绪时按个股）。"""
    _, positions, _ = accounts.get_snapshot(db)
    if not positions:
        return {"granularity": "none", "today_pnl": 0.0, "base": 0.0, "items": []}
    quotes = market.get_realtime_quotes([p.code for p in positions]) if positions else {}
    strategies = db.query(Strategy).all()
    cash = sum(s.available_cash or 0.0 for s in strategies)
    industry_data = industry_map.get_industry_map()
    granularity = "industry" if industry_data else "stock"

    per_item = []
    market_value_before = 0.0
    for p in positions:
        rt = quotes.get(p.code)
        if not rt or (rt.get("prev_close") or 0) <= 0:
            continue
        pnl = p.qty * (rt["price"] - rt["prev_close"])
        market_value_before += p.qty * rt["prev_close"]
        label = industry_data.get(p.code, p.name) if granularity == "industry" else p.name
        per_item.append({"code": p.code, "name": p.name, "label": label, "pnl": round(pnl, 2)})

    base = cash + market_value_before
    today_pnl = sum(x["pnl"] for x in per_item)
    groups: dict[str, float] = {}
    for x in per_item:
        groups[x["label"]] = groups.get(x["label"], 0.0) + x["pnl"]

    items = [
        {"label": label, "pnl": round(pnl, 2),
         "pct": round(pnl / base * 100, 2) if base else 0.0}
        for label, pnl in sorted(groups.items(), key=lambda kv: abs(kv[1]), reverse=True)
    ]
    return {
        "granularity": granularity,
        "today_pnl": round(today_pnl, 2),
        "base": round(base, 2),
        "items": items,
    }


@app.get("/api/alerts")
def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """预警提醒列表（最近 N 条，默认 50，上限 500）。"""
    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    limit = max(1, min(int(limit), 500))
    alerts = db.query(Alert).filter(Alert.account_id == acct.id).order_by(Alert.id.desc()).limit(limit).all()
    return [
        {
            "id": a.id, "code": a.code, "name": a.name, "type": a.alert_type,
            "message": a.message, "price": a.price,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@app.get("/api/positions")
def get_positions(db: Session = Depends(get_db)):
    _, positions, _ = accounts.get_snapshot(db)
    strategy_names = {s.id: s.name for s in db.query(Strategy).all()}
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=10)).isoformat()
    quotes = market.get_realtime_quotes([p.code for p in positions]) if positions else {}
    result = []
    for p in positions:
        price = p.avg_cost
        rt = quotes.get(p.code)
        if rt:
            price = rt["price"]
        else:
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
            "strategy_id": p.strategy_id,
            "strategy_name": strategy_names.get(p.strategy_id) if p.strategy_id else None,
        })
    return result


@app.get("/api/trades")
def get_trades(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    q = db.query(Trade).filter(Trade.account_id == acct.id)
    total = q.count()
    trades = q.order_by(Trade.id.desc()).offset(offset).limit(limit).all()
    items = [
        {
            "id": t.id, "code": t.code, "name": t.name, "direction": t.direction,
            "qty": t.qty, "price": t.price, "commission": round(t.commission, 2),
            "tax": round(t.tax, 2), "pnl": round(t.pnl, 2),
            "traded_at": t.traded_at.isoformat() if t.traded_at else None,
        }
        for t in trades
    ]
    all_rows = q.all()
    sells = [t for t in all_rows if t.direction == "sell"]
    summary = {
        "total": total,
        "buys": sum(1 for t in all_rows if t.direction == "buy"),
        "sells": len(sells),
        "pnl": round(sum(t.pnl or 0 for t in all_rows), 2),
        "wins": sum(1 for t in sells if (t.pnl or 0) > 0),
        "losses": sum(1 for t in sells if (t.pnl or 0) < 0),
    }
    return {"items": items, "total": total, "has_more": offset + len(items) < total, "summary": summary}


@app.get("/api/orders")
def get_orders(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """委托列表（分页，按 id 倒序）。"""
    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    q = db.query(Order).filter(Order.account_id == acct.id)
    total = q.count()
    orders = q.order_by(Order.id.desc()).offset(offset).limit(limit).all()
    items = [
        {
            "id": o.id, "code": o.code, "name": o.name, "direction": o.direction,
            "qty": o.qty, "price": o.price, "status": o.status, "reason": o.reason,
            "broker_type": o.broker_type or "paper",
            "external_order_id": o.external_order_id,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]
    return {"items": items, "total": total, "has_more": offset + len(items) < total}


# ===== 实盘下单二次确认（确认链路与下单链路解耦） =====
_pending_orders = {}
_pending_lock = threading.Lock()
_PENDING_TTL = 300


@app.post("/api/orders/prepare")
def prepare_order(body: OrderPrepareRequest):
    """阶段一：提交下单请求，返回 request_id 供用户确认。"""
    request_id = uuid.uuid4().hex
    payload = body.model_dump()
    with _pending_lock:
        _pending_orders[request_id] = {"body": payload, "created_at": time.time()}
    return {"request_id": request_id, "status": "pending", "order": payload}


@app.post("/api/orders/confirm/{request_id}")
def confirm_order(request_id: str, db: Session = Depends(get_db)):
    """阶段二：确认下发，真正调用券商下单。"""
    with _pending_lock:
        item = _pending_orders.pop(request_id, None)
    if not item or time.time() - item["created_at"] > _PENDING_TTL:
        raise HTTPException(404, "下单请求不存在或已过期")
    body = item["body"]
    strategy = None
    if body.get("strategy_id"):
        strategy = db.query(Strategy).filter(Strategy.id == body["strategy_id"]).first()
        if not strategy:
            raise HTTPException(404, "策略不存在")
    _check_order_limits(db, body)
    broker = get_broker(config.BROKER_TYPE)
    order = broker.place_order(
        db, body["code"], body["name"], body["direction"],
        body["price"], body["qty"], body.get("reason", ""), strategy=strategy)
    return {"status": order.status, "reason": order.reason, "order_id": order.id}


def _check_order_limits(db: Session, body: dict):
    """实盘模式下校验单笔与单日累计委托金额上限。"""
    if config.BROKER_TYPE != "live":
        return
    amount = float(body.get("price", 0)) * int(body.get("qty", 0))
    if amount > config.MAX_SINGLE_ORDER_AMOUNT:
        raise HTTPException(400, f"单笔委托金额 {amount:.2f} 超过上限 {config.MAX_SINGLE_ORDER_AMOUNT:.2f}")
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_sum = db.query(func.coalesce(func.sum(Order.price * Order.qty), 0.0)).filter(
        Order.broker_type == "live",
        Order.status == "filled",
        Order.created_at >= today_start,
    ).scalar()
    if float(daily_sum) + amount > config.MAX_DAILY_ORDER_AMOUNT:
        raise HTTPException(400, f"单日累计委托金额将超过上限 {config.MAX_DAILY_ORDER_AMOUNT:.2f}")


@app.get("/api/indices")
def get_indices():
    """三大指数实时行情（上证指数/深证成指/创业板指）。"""
    try:
        return market.get_index_quotes()
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))


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


@app.post("/api/stocks/{code}/diagnose")
def diagnose_stock(code: str, db: Session = Depends(get_db)):
    """AI 个股技术诊断：基于日线技术指标调用智能体，未配置 LLM 时启发式降级。"""
    from .agents import stock_diagnosis
    from .indicators import compute_indicators

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=300)).isoformat()
    try:
        bars = market.get_daily_bars(code, start, end)
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))
    if bars is None or len(bars) < 30:
        raise HTTPException(404, "行情数据不足，无法诊断")
    ind = compute_indicators(bars)
    if not ind:
        raise HTTPException(404, "行情数据不足，无法诊断")

    name = code
    try:
        names = market.get_stock_names([code])
        name = names.get(code, code)
    except Exception:
        pass

    context = {
        "code": code,
        "name": name,
        "price": ind.get("price"),
        "recent_high": ind.get("recent_high"),
        "recent_low": ind.get("recent_low"),
        "indicators": ind,
    }
    return stock_diagnosis(context)


@app.post("/api/scan")
def trigger_scan(db: Session = Depends(get_db)):
    """手动触发一次全市场扫描交易。"""
    if not scan_lock.acquire(blocking=False):
        raise HTTPException(409, "已有扫描正在进行，请稍后再试")
    try:
        report = scan_and_trade(db, market, accounts)
        return report
    finally:
        scan_lock.release()


@app.post("/api/scan/stream")
def trigger_scan_stream():
    """流式扫描交易：NDJSON 逐行输出进度事件，末行输出完整报告。"""
    q = queue.Queue()

    def progress(stage, message, done, total):
        q.put({"type": "progress", "stage": stage, "message": message,
               "done": done, "total": total})

    def busy_gen():
        yield json.dumps({"type": "error", "detail": "已有扫描正在进行，请稍后再试",
                          "status": 409}, ensure_ascii=False) + "\n"

    if not scan_lock.acquire(blocking=False):
        return StreamingResponse(busy_gen(), media_type="application/x-ndjson")

    def worker():
        db = SessionLocal()
        try:
            report = scan_and_trade(db, market, accounts, source="manual", progress=progress)
            q.put({"type": "result", "report": report})
        except Exception as exc:
            q.put({"type": "error", "detail": str(exc), "status": 500})
        finally:
            db.close()
            scan_lock.release()

    threading.Thread(target=worker, daemon=True).start()

    def gen():
        while True:
            evt = q.get()
            if evt["type"] == "error":
                yield json.dumps(evt, ensure_ascii=False) + "\n"
                break
            if evt["type"] == "result":
                yield json.dumps(evt, ensure_ascii=False) + "\n"
                break
            yield json.dumps(evt, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.post("/api/screener")
def screen_stocks(body: dict, db: Session = Depends(get_db)):
    """条件选股：基于全市场实时行情按价格/涨跌幅/换手率/市值/成交额筛选排序。"""
    try:
        quotes = market.get_market_quotes()
    except DataUnavailableError as exc:
        raise HTTPException(502, str(exc))

    f = body or {}

    def num(v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    price_min, price_max = num(f.get("price_min")), num(f.get("price_max"))
    chg_min, chg_max = num(f.get("change_pct_min")), num(f.get("change_pct_max"))
    to_min, to_max = num(f.get("turnover_min")), num(f.get("turnover_max"))
    mc_min, mc_max = num(f.get("market_cap_min")), num(f.get("market_cap_max"))
    amt_min, amt_max = num(f.get("amount_min")), num(f.get("amount_max"))

    out = []
    for q in quotes:
        if price_min is not None and q["price"] < price_min:
            continue
        if price_max is not None and q["price"] > price_max:
            continue
        if chg_min is not None and q["change_pct"] < chg_min:
            continue
        if chg_max is not None and q["change_pct"] > chg_max:
            continue
        if to_min is not None and q["turnover"] < to_min:
            continue
        if to_max is not None and q["turnover"] > to_max:
            continue
        if mc_min is not None and q["market_cap"] < mc_min:
            continue
        if mc_max is not None and q["market_cap"] > mc_max:
            continue
        if amt_min is not None and q["amount"] < amt_min:
            continue
        if amt_max is not None and q["amount"] > amt_max:
            continue
        out.append(q)

    sorters = {
        "change_pct": lambda x: x["change_pct"],
        "turnover": lambda x: x["turnover"],
        "market_cap": lambda x: x["market_cap"],
        "amount": lambda x: x["amount"],
        "price": lambda x: x["price"],
    }
    sort_by = f.get("sort_by", "change_pct")
    out.sort(key=sorters.get(sort_by, sorters["change_pct"]),
             reverse=f.get("sort_dir", "desc") != "asc")

    limit = max(1, min(int(f.get("limit") or 50), 200))
    return {
        "total": len(out),
        "updated_at": datetime.now().strftime("%H:%M:%S"),
        "items": out[:limit],
    }


@app.get("/api/scan/reports")
def list_scan_reports(db: Session = Depends(get_db)):
    """查询扫描统计与历史报告（统计为全量累计，明细为最近 20 条）。"""
    total_scans, total_buys, total_sells, total_rejects = db.query(
        func.count(ScanReport.id),
        func.coalesce(func.sum(ScanReport.buy_count), 0),
        func.coalesce(func.sum(ScanReport.sell_count), 0),
        func.coalesce(func.sum(ScanReport.reject_count), 0),
    ).one()
    items = db.query(ScanReport).order_by(ScanReport.id.desc()).limit(20).all()
    return {
        "scan_schedule": {
            "hour": config.SCAN_HOUR,
            "minute": config.SCAN_MINUTE,
            "broker_type": config.BROKER_TYPE,
        },
        "stats": {
            "total_scans": total_scans,
            "total_buys": total_buys,
            "total_sells": total_sells,
            "total_rejects": total_rejects,
        },
        "items": [{
            "id": r.id,
            "strategy_count": r.strategy_count,
            "buy_count": r.buy_count,
            "sell_count": r.sell_count,
            "reject_count": r.reject_count,
            "source": r.source or "manual",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in items],
    }


@app.get("/api/scan/reports/{rid}")
def get_scan_report(rid: int, db: Session = Depends(get_db)):
    """查询某次扫描的完整报告（买入/卖出/拒绝明细与理由）。"""
    r = db.query(ScanReport).filter(ScanReport.id == rid).first()
    if not r:
        raise HTTPException(404, "扫描报告不存在")
    return json.loads(r.report_json or "{}")


@app.post("/api/account/reset")
def reset_account(db: Session = Depends(get_db)):
    """重置模拟账户：清空持仓、订单与成交，各策略资金恢复其分配本金。"""
    from .models import Order, Position, Trade

    acct = accounts.ensure_account(db, config.DEFAULT_INITIAL_CAPITAL)
    db.query(Position).filter(Position.account_id == acct.id).delete()
    db.query(Trade).filter(Trade.account_id == acct.id).delete()
    db.query(Order).filter(Order.account_id == acct.id).delete()
    acct.available_cash = acct.initial_capital
    for s in db.query(Strategy).all():
        capital = s.initial_capital or config.DEFAULT_INITIAL_CAPITAL
        s.initial_capital = capital
        s.available_cash = capital
    db.commit()
    return {"ok": True}


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="/workspace", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
