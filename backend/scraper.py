"""
scraper.py
负责从网易 BUFF 公开接口抓取指定饰品的价格信息。
"""
import time
import logging
from typing import Optional, Dict, List

import requests

logger = logging.getLogger(__name__)


class BuffScraper:
    """BUFF 价格抓取器。"""

    BASE_URL = "https://buff.163.com"
    SELL_ORDER_URL = f"{BASE_URL}/api/market/goods/sell_order"
    PRICE_HISTORY_URL = f"{BASE_URL}/api/market/goods/price_history/buff/v2"

    def __init__(self, goods_id: int, game: str = "csgo",
                 user_agent: str = "", timeout: int = 10,
                 interval: int = 3, cookie: str = ""):
        self.goods_id = goods_id
        self.game = game
        self.timeout = timeout
        self.interval = interval
        self.session = requests.Session()
        headers = {
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://buff.163.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if cookie:
            headers["Cookie"] = cookie
        self.session.headers.update(headers)

    def _ts(self) -> int:
        """生成 BUFF 接口需要的 _ 时间戳（毫秒）。"""
        return int(round(time.time() * 1000))

    def fetch_lowest_sell_price(self) -> Optional[Dict]:
        """
        获取在售订单中最低的售价。
        返回示例：{"price": 1234.5, "goods_id": 781593, "count": 12}
        失败时返回 None。
        """
        params = {
            "game": self.game,
            "goods_id": self.goods_id,
            "page_num": 1,
            "sort_by": "price.asc",
            "mode": "",
            "allow_tradable_cooldown": 1,
            "_": self._ts(),
        }
        try:
            resp = self.session.get(
                self.SELL_ORDER_URL, params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("请求 BUFF 在售订单失败: %s", e)
            return None

        if data.get("code") != "OK":
            logger.error("BUFF 返回错误: %s", data)
            return None

        items = (data.get("data") or {}).get("items") or []
        if not items:
            logger.warning("BUFF 未返回在售订单，物品可能暂时下架。")
            return {
                "price": None,
                "goods_id": self.goods_id,
                "count": 0,
                "min_price": None,
                "max_price": None,
            }

        prices = [float(it.get("price", 0)) for it in items if it.get("price")]
        if not prices:
            return None

        prices.sort()
        return {
            "price": prices[0],
            "goods_id": self.goods_id,
            "count": len(items),
            "min_price": prices[0],
            "max_price": prices[-1],
        }

    def fetch_price_history(self, days: int = 30) -> List[Dict]:
        """
        获取历史价格曲线（BUFF 自带的历史价格接口）。
        返回格式：[{"date": "2026-07-20", "price": 1234.5}, ...]
        """
        params = {
            "game": self.game,
            "goods_id": self.goods_id,
            "currency": "CNY",
            "days": days,
            "_": self._ts(),
        }
        try:
            resp = self.session.get(
                self.PRICE_HISTORY_URL, params=params, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("请求 BUFF 历史价格失败: %s", e)
            return []

        if data.get("code") != "OK":
            logger.error("BUFF 历史价格返回错误: %s", data)
            return []

        # 历史价格字段名在不同版本中可能是 price 或 data
        raw = data.get("data") or {}
        points = raw.get("price") or raw.get("data") or []
        result: List[Dict] = []
        for p in points:
            # 兼容 [timestamp, price] 或 {date, price} 两种格式
            if isinstance(p, dict):
                date = p.get("date") or p.get("time") or ""
                price = p.get("price")
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                ts, price = p[0], p[1]
                try:
                    date = time.strftime(
                        "%Y-%m-%d", time.localtime(int(ts) / 1000)
                    )
                except Exception:
                    date = str(ts)
            else:
                continue
            try:
                result.append({
                    "date": date,
                    "price": float(price),
                })
            except (TypeError, ValueError):
                continue
        return result

    def polite_sleep(self):
        """两次请求之间的礼貌等待。"""
        time.sleep(self.interval)
