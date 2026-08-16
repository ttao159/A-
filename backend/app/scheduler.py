"""定时调度：交易日收盘后自动扫描交易。"""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .account import AccountService
from .database import SessionLocal
from .market import MarketDataService
from .scanner import scan_and_trade, scan_lock

logger = logging.getLogger("scheduler")


def _run_scan():
    if not scan_lock.acquire(blocking=False):
        logger.info("已有扫描在进行，跳过本次自动扫描")
        return
    db = SessionLocal()
    try:
        report = scan_and_trade(db, MarketDataService(), AccountService(), source="auto")
        logger.info("自动扫描完成: 买入 %s 笔, 卖出 %s 笔, 拒绝 %s 笔",
                    len(report.get("buys", [])),
                    len(report.get("sells", [])),
                    len(report.get("rejected", [])))
    except Exception as e:  # noqa: BLE001
        logger.exception("自动扫描失败: %s", e)
    finally:
        db.close()
        scan_lock.release()


def start_scheduler() -> BackgroundScheduler:
    tz = ZoneInfo("Asia/Shanghai")
    scheduler = BackgroundScheduler(timezone=tz)
    scheduler.add_job(
        _run_scan,
        CronTrigger(day_of_week="mon-fri", hour=config.SCAN_HOUR, minute=config.SCAN_MINUTE, timezone=tz),
        id="daily_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("调度器已启动：每个工作日 %02d:%02d 执行扫描", config.SCAN_HOUR, config.SCAN_MINUTE)
    return scheduler
