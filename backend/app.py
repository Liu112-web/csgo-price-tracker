"""
app.py
基于 FastAPI 的数据接口，供前端折线图与仪表盘使用。
支持生产环境提供前端静态文件服务。
"""
import json
import logging
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database
from scheduler import run_once

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()
database.init_db()

app = FastAPI(title="CSGO 弯刀 传说 价格监控 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigModel(BaseModel):
    goods_id: int
    item_name: str
    target_price: float
    purchase_price: float
    check_time: str
    api_host: str
    api_port: int
    price_history_days: int = 30
    request_interval_seconds: int = 3
    request_timeout_seconds: int = 10
    cookie: str = ""
    user_agent: str = ""


class PricePoint(BaseModel):
    date: str
    price: float


@app.get("/api/config")
def get_config():
    return CFG


@app.post("/api/config")
def update_config(new_cfg: ConfigModel):
    global CFG
    CFG = new_cfg.dict()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(CFG, f, ensure_ascii=False, indent=2)
    return {"ok": True, "config": CFG}


@app.get("/api/price/latest")
def get_latest():
    row = database.get_latest_price(CFG["goods_id"])
    return {
        "goods_id": CFG["goods_id"],
        "item_name": CFG.get("item_name", ""),
        "target_price": CFG.get("target_price"),
        "purchase_price": CFG.get("purchase_price"),
        "latest": row,
    }


@app.get("/api/price/daily")
def get_daily():
    rows = database.get_daily_prices(CFG["goods_id"])
    return {
        "goods_id": CFG["goods_id"],
        "points": rows,
    }


@app.get("/api/price/history")
def get_history():
    rows = database.get_history_prices(CFG["goods_id"], source="buff_history")
    return {
        "goods_id": CFG["goods_id"],
        "points": rows,
    }


@app.get("/api/alerts")
def get_alerts():
    rows = database.get_recent_alerts(CFG["goods_id"], limit=50)
    return {"alerts": rows}


@app.post("/api/check/now")
def trigger_check_now():
    summary = run_once(CFG)
    return {"ok": True, "summary": summary}


DIST_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")
if os.path.exists(DIST_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(DIST_DIR, "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    @app.get("/")
    async def root():
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "CSGO 弯刀 传说 价格监控",
            "docs": "/docs",
        }
