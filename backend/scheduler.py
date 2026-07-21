"""
scheduler.py
每天定时执行一次价格抓取与提醒。
"""
import logging
import threading
import time
from datetime import datetime

import schedule

from database import (
    upsert_daily_price, insert_history, log_check, log_alert,
    has_alerted_today,
)
from notifier import notify_price_alert
from scraper import BuffScraper

logger = logging.getLogger(__name__)


def run_once(cfg: dict) -> dict:
    """执行一次抓取 + 存储 + 提醒。返回本次执行结果摘要。"""
    goods_id = cfg["goods_id"]
    item_name = cfg.get("item_name", f"goods_id={goods_id}")
    target_price = float(cfg.get("target_price", 690))

    scraper = BuffScraper(
        goods_id=goods_id,
        user_agent=cfg.get("user_agent", ""),
        timeout=cfg.get("request_timeout_seconds", 10),
        interval=cfg.get("request_interval_seconds", 3),
        cookie=cfg.get("cookie", ""),
    )

    logger.info("开始抓取 goods_id=%s 的价格...", goods_id)
    summary = {"success": False, "price": None, "alerted": False}

    # 1) 抓取最低在售价
    info = scraper.fetch_lowest_sell_price()
    if info and info.get("price") is not None:
        price = float(info["price"])
        upsert_daily_price(
            goods_id=goods_id,
            price=price,
            min_price=info.get("min_price"),
            max_price=info.get("max_price"),
            listing_count=info.get("count"),
        )
        log_check(goods_id, True, price, "ok")
        summary.update({"success": True, "price": price})
        logger.info("当前最低在售价: ¥%.2f (在售 %d 件)",
                    price, info.get("count", 0))

        # 2) 判断是否触发提醒
        if price > target_price:
            if not has_alerted_today(goods_id, target_price):
                alerted = notify_price_alert(item_name, price, target_price)
                log_alert(goods_id, price, target_price,
                          f"price>{target_price}")
                summary["alerted"] = True
                logger.warning("已触发提醒: ¥%.2f > ¥%.2f", price, target_price)
            else:
                logger.info("今天已经提醒过，不再重复推送。")
        else:
            logger.info("未超过目标价 (¥%.2f)，无需提醒。", target_price)
    else:
        log_check(goods_id, False, None, "no_price_data")
        logger.warning("本次未拿到有效价格。")

    # 3) 拉取历史价格曲线（用于折线图背景）
    try:
        days = int(cfg.get("price_history_days", 30))
        history = scraper.fetch_price_history(days=days)
        if history:
            insert_history(goods_id, history, source="buff_history")
            logger.info("已写入 %d 条历史价格点。", len(history))
    except Exception as e:
        logger.warning("获取历史价格失败: %s", e)

    return summary


def start_scheduler(cfg: dict, run_immediately: bool = True) -> None:
    """在子线程中启动 schedule 循环。"""
    check_time = cfg.get("check_time", "20:00")

    def job():
        try:
            run_once(cfg)
        except Exception as e:
            logger.exception("定时任务执行失败: %s", e)

    schedule.every().day.at(check_time).do(job)
    logger.info("已注册每日 %s 的抓取任务。", check_time)

    if run_immediately:
        logger.info("启动后立即执行一次...")
        threading.Thread(target=job, daemon=True).start()

    stop_event = threading.Event()

    def loop():
        while not stop_event.is_set():
            schedule.run_pending()
            time.sleep(20)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return stop_event
