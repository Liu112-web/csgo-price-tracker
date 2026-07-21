"""
database.py
使用 SQLite 存储每日抓取到的最低在售价与历史价格。
"""
import os
import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "prices.db")


def ensure_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_conn():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据表。"""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goods_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                price REAL,
                min_price REAL,
                max_price REAL,
                listing_count INTEGER,
                created_at TEXT NOT NULL,
                UNIQUE(goods_id, date)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goods_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                price REAL NOT NULL,
                source TEXT DEFAULT 'buff_history',
                created_at TEXT NOT NULL,
                UNIQUE(goods_id, date, source)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goods_id INTEGER NOT NULL,
                price REAL NOT NULL,
                target_price REAL NOT NULL,
                triggered_at TEXT NOT NULL,
                message TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS check_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goods_id INTEGER NOT NULL,
                checked_at TEXT NOT NULL,
                success INTEGER NOT NULL,
                price REAL,
                message TEXT
            )
        """)
    logger.info("数据库已就绪: %s", DB_PATH)


def upsert_daily_price(goods_id: int, price: float,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       listing_count: Optional[int] = None,
                       day: Optional[str] = None) -> None:
    """插入或更新某天的最低在售价。"""
    day = day or date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO price_daily
                (goods_id, date, price, min_price, max_price, listing_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(goods_id, date) DO UPDATE SET
                price=excluded.price,
                min_price=excluded.min_price,
                max_price=excluded.max_price,
                listing_count=excluded.listing_count,
                created_at=excluded.created_at
        """, (goods_id, day, price, min_price, max_price, listing_count, now))


def insert_history(goods_id: int, points: List[Dict],
                   source: str = "buff_history") -> int:
    """批量写入历史价格点。返回成功写入条数。"""
    if not points:
        return 0
    now = datetime.now().isoformat(timespec="seconds")
    rows = [(goods_id, p["date"], float(p["price"]), source, now)
            for p in points if p.get("date") and p.get("price") is not None]
    with get_conn() as conn:
        c = conn.cursor()
        c.executemany("""
            INSERT OR IGNORE INTO price_history
                (goods_id, date, price, source, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, rows)
        return c.rowcount


def log_check(goods_id: int, success: bool, price: Optional[float],
              message: str = "") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO check_log (goods_id, checked_at, success, price, message)
            VALUES (?, ?, ?, ?, ?)
        """, (goods_id, now, 1 if success else 0, price, message))


def log_alert(goods_id: int, price: float, target_price: float,
              message: str = "") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO alert_log (goods_id, price, target_price,
                                   triggered_at, message)
            VALUES (?, ?, ?, ?, ?)
        """, (goods_id, price, target_price, now, message))


def get_daily_prices(goods_id: int, limit: int = 365) -> List[Dict]:
    """返回按日期升序的日级价格列表。"""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT date, price, min_price, max_price, listing_count, created_at
            FROM price_daily
            WHERE goods_id = ?
            ORDER BY date ASC
            LIMIT ?
        """, (goods_id, limit))
        return [dict(row) for row in c.fetchall()]


def get_history_prices(goods_id: int, source: str = "buff_history",
                       limit: int = 400) -> List[Dict]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT date, price
            FROM price_history
            WHERE goods_id = ? AND source = ?
            ORDER BY date ASC
            LIMIT ?
        """, (goods_id, source, limit))
        return [dict(row) for row in c.fetchall()]


def get_latest_price(goods_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT date, price, min_price, max_price, listing_count, created_at
            FROM price_daily
            WHERE goods_id = ?
            ORDER BY date DESC
            LIMIT 1
        """, (goods_id,))
        row = c.fetchone()
        return dict(row) if row else None


def get_recent_alerts(goods_id: int, limit: int = 20) -> List[Dict]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT price, target_price, triggered_at, message
            FROM alert_log
            WHERE goods_id = ?
            ORDER BY triggered_at DESC
            LIMIT ?
        """, (goods_id, limit))
        return [dict(row) for row in c.fetchall()]


def has_alerted_today(goods_id: int, target_price: float) -> bool:
    """判断今天是否已经为该目标价发送过提醒（避免重复打扰）。"""
    today = date.today().isoformat()
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 1 FROM alert_log
            WHERE goods_id = ?
              AND target_price = ?
              AND substr(triggered_at, 1, 10) = ?
            LIMIT 1
        """, (goods_id, target_price, today))
        return c.fetchone() is not None
