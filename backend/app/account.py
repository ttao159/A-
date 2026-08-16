"""账户服务：核心组合逻辑（内存 Portfolio）与 DB 持久化账户。"""

from datetime import date, datetime

from . import config, matching
from .models import Account, AccountEquityPoint, Order, Position, Trade


def check_risk(state: dict, config: dict, price: float, qty: int, prices: dict):
    """开仓风控检查。state 含 initial_capital/cash/positions/high_water。

    返回 (ok: bool, reason: str)。
    """
    risk = config.get("risk", {})
    max_holdings = int(risk.get("maxHoldings", 10))
    max_pos_pct = float(risk.get("maxPositionPercent", 20))
    total_stop = float(risk.get("totalStopLoss", 20))
    max_drawdown = float(risk.get("maxDrawdown", 25))

    if len(state["positions"]) >= max_holdings:
        return False, "达到最大持仓数量"

    equity = state["cash"] + sum(
        p["qty"] * prices.get(p["code"], p["avg_cost"]) for p in state["positions"].values()
    )
    if equity <= 0:
        return False, "资产异常"
    if price * qty / equity > max_pos_pct / 100.0:
        return False, "超过单只股票最大仓位"

    if state["initial_capital"] > 0 and \
            (equity - state["initial_capital"]) / state["initial_capital"] * 100.0 <= -total_stop:
        return False, "触发组合止损线"

    if state["high_water"] > 0 and \
            (state["high_water"] - equity) / state["high_water"] * 100.0 >= max_drawdown:
        return False, "触发最大回撤限制"

    return True, ""


class Portfolio:
    """内存组合，供回测使用。"""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}          # code -> dict
        self.trades = []
        self.high_water = initial_capital
        self.total_realized_pnl = 0.0

    def state(self):
        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "positions": self.positions,
            "high_water": self.high_water,
        }

    def equity(self, prices: dict) -> float:
        mv = sum(p["qty"] * prices.get(p["code"], p["avg_cost"]) for p in self.positions.values())
        return self.cash + mv

    def buy(self, code: str, name: str, price: float, qty: int, date: str, reason: str = ""):
        qty = matching.round_lot(qty)
        if qty < 100:
            return None
        commission, tax, transfer = matching.calc_fees("buy", price, qty)
        total_cost = price * qty + commission + transfer
        if total_cost > self.cash:
            qty = matching.round_lot(int(self.cash / (price * 1.001)))
            if qty < 100:
                return None
            commission, tax, transfer = matching.calc_fees("buy", price, qty)
            total_cost = price * qty + commission + transfer

        self.cash -= total_cost
        pos = self.positions.get(code)
        if pos:
            new_qty = pos["qty"] + qty
            pos["avg_cost"] = (pos["avg_cost"] * pos["qty"] + price * qty + commission + transfer) / new_qty
            pos["qty"] = new_qty
            pos["hold_days"] = 0
        else:
            self.positions[code] = {
                "code": code, "name": name, "qty": qty,
                "avg_cost": (price * qty + commission + transfer) / qty,
                "hold_days": 0, "high_since_buy": price,
            }
        self.trades.append({
            "date": date, "code": code, "name": name, "direction": "buy",
            "qty": qty, "price": price, "pnl": 0.0, "reason": reason,
        })
        return qty

    def sell(self, code: str, price: float, qty: int, date: str, reason: str = ""):
        pos = self.positions.get(code)
        if not pos:
            return None
        qty = min(qty, pos["qty"])
        if qty <= 0:
            return None
        commission, tax, transfer = matching.calc_fees("sell", price, qty)
        proceeds = price * qty - commission - tax - transfer
        pnl = (price - pos["avg_cost"]) * qty - commission - tax - transfer
        self.cash += proceeds
        self.total_realized_pnl += pnl
        pos["qty"] -= qty
        if pos["qty"] == 0:
            del self.positions[code]
        self.trades.append({
            "date": date, "code": code, "name": pos["name"], "direction": "sell",
            "qty": qty, "price": price, "pnl": pnl, "reason": reason,
        })
        return qty

    def update_daily(self, prices: dict):
        """每个交易日收盘后更新持仓持有天数与期间最高价。"""
        for p in self.positions.values():
            p["hold_days"] += 1
            price = prices.get(p["code"], p["high_since_buy"])
            p["high_since_buy"] = max(p["high_since_buy"], price)
        equity = self.equity(prices)
        self.high_water = max(self.high_water, equity)


class AccountService:
    """DB 持久化的模拟账户服务。"""

    def ensure_account(self, db, initial_capital: float):
        acct = db.query(Account).first()
        if not acct:
            acct = Account(initial_capital=initial_capital, available_cash=initial_capital)
            db.add(acct)
            db.commit()
            db.refresh(acct)
        return acct

    def get_snapshot(self, db):
        acct = self.ensure_account(db, 1_000_000.0)
        positions = db.query(Position).filter(Position.account_id == acct.id).all()
        trades = db.query(Trade).filter(Trade.account_id == acct.id).order_by(Trade.id.desc()).limit(50).all()
        return acct, positions, trades

    def record_equity(self, db, acct, total: float):
        """按日记录账户总资产，供资金曲线展示（同日覆盖）。"""
        today = date.today().isoformat()
        pt = db.query(AccountEquityPoint).filter_by(account_id=acct.id, date=today).first()
        if pt:
            pt.equity = round(total, 2)
        else:
            db.add(AccountEquityPoint(account_id=acct.id, date=today, equity=round(total, 2)))
        db.commit()

    def equity_curve(self, db, acct, limit: int = 60):
        pts = (
            db.query(AccountEquityPoint)
            .filter(AccountEquityPoint.account_id == acct.id)
            .order_by(AccountEquityPoint.date.desc())
            .limit(limit)
            .all()
        )
        pts = list(reversed(pts))
        return [{"date": p.date, "equity": p.equity} for p in pts]

    def daily_pnl(self, db, acct, limit: int = 120):
        """按日计算盈亏（当日权益 - 前一日权益），供收益日历展示。"""
        curve = self.equity_curve(db, acct, limit=limit)
        result = []
        prev_equity = None
        for pt in curve:
            pnl = round(pt["equity"] - prev_equity, 2) if prev_equity is not None else 0.0
            result.append({"date": pt["date"], "equity": pt["equity"], "pnl": pnl})
            prev_equity = pt["equity"]
        return result

    def roll_daily(self, db):
        """每个新交易日开始时，将持仓持有天数 +1（用于 T+1 与持有天数信号）。"""
        today = date.today()
        positions = db.query(Position).all()
        changed = False
        for p in positions:
            if p.updated_at is None or p.updated_at.date() < today:
                p.hold_days = (p.hold_days or 0) + 1
                p.updated_at = datetime.utcnow()
                changed = True
        if changed:
            db.commit()

    def ensure_strategy_capital(self, db, acct, strategies):
        """确保每个启用策略拥有独立本金：未分配本金的策略默认 100 万，各自独立运作。

        每个策略独立计算，账户级现金不再参与策略资金分配。
        """
        if not strategies:
            return
        changed = False
        for s in strategies:
            if (s.initial_capital or 0.0) <= 0:
                s.initial_capital = config.DEFAULT_INITIAL_CAPITAL
                s.available_cash = config.DEFAULT_INITIAL_CAPITAL
                changed = True
        if changed:
            db.commit()

    def place_order(self, db, acct, code, name, direction, price, qty, reason="", strategy=None):
        """手动/自动下单并撮合成交。

        strategy 提供时，按该策略的独立现金与持仓运作；否则使用账户级现金与持仓。
        """
        order = Order(account_id=acct.id, code=code, name=name,
                      direction=direction, qty=qty, price=price,
                      status="filled", reason=reason)
        db.add(order)
        db.flush()

        commission, tax, transfer = matching.calc_fees(direction, price, qty)
        if strategy is not None:
            cash_holder = strategy
            pos_filter = {"account_id": acct.id, "strategy_id": strategy.id, "code": code}
        else:
            cash_holder = acct
            pos_filter = {"account_id": acct.id, "code": code}

        if direction == "buy":
            total_cost = price * qty + commission + transfer
            if total_cost > cash_holder.available_cash:
                order.status = "rejected"
                order.reason = "可用资金不足"
                db.commit()
                return order
            cash_holder.available_cash -= total_cost
            pos = db.query(Position).filter_by(**pos_filter).first()
            if pos:
                new_qty = pos.qty + qty
                pos.avg_cost = (pos.avg_cost * pos.qty + price * qty + commission + transfer) / new_qty
                pos.qty = new_qty
                pos.hold_days = 0
                pos.high_since_buy = price
            else:
                pos_kwargs = dict(account_id=acct.id, code=code, name=name, qty=qty,
                                  avg_cost=(price * qty + commission + transfer) / qty,
                                  hold_days=0, high_since_buy=price)
                if strategy is not None:
                    pos_kwargs["strategy_id"] = strategy.id
                db.add(Position(**pos_kwargs))
            pnl = 0.0
        else:
            pos = db.query(Position).filter_by(**pos_filter).first()
            if not pos or pos.qty < qty:
                order.status = "rejected"
                order.reason = "持仓不足"
                db.commit()
                return order
            proceeds = price * qty - commission - tax - transfer
            pnl = (price - pos.avg_cost) * qty - commission - tax - transfer
            cash_holder.available_cash += proceeds
            pos.qty -= qty
            if pos.qty == 0:
                db.delete(pos)

        db.add(Trade(order_id=order.id, account_id=acct.id,
                     strategy_id=strategy.id if strategy is not None else None,
                     code=code, name=name, direction=direction, qty=qty, price=price,
                     commission=commission, tax=tax, transfer_fee=transfer, pnl=pnl))
        db.commit()
        db.refresh(order)
        return order
