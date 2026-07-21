"""
main.py
生产环境启动：后端 API + 前端静态文件服务 + 定时任务。
"""
import json
import logging
import os
import sys
import threading
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_config()
    logger.info("=" * 60)
    logger.info("CSGO 弯刀 传说 价格监控服务启动")
    logger.info("物品: %s", cfg.get("item_name"))
    logger.info("目标价: ¥%.2f / 购入价: ¥%.2f",
                cfg.get("target_price", 0), cfg.get("purchase_price", 0))
    logger.info("每日抓取时间: %s", cfg.get("check_time", "20:00"))
    logger.info("API 端口: %s:%s", cfg.get("api_host"), cfg.get("api_port"))
    logger.info("=" * 60)

    import database
    database.init_db()

    from scheduler import start_scheduler, run_once

    def first_fetch():
        try:
            logger.info("后台首次抓取开始...")
            run_once(cfg)
            logger.info("后台首次抓取完成。")
        except Exception as e:
            logger.exception("首次抓取失败: %s", e)

    threading.Thread(target=first_fetch, daemon=True).start()

    start_scheduler(cfg, run_immediately=False)

    logger.info("API 服务正在启动...")
    from app import app as fastapi_app

    port = int(os.environ.get("PORT", cfg.get("api_port", 8765)))
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，退出。")
        sys.exit(0)
