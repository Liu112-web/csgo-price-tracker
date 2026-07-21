# CSGO 弯刀 传说 久经沙场 价格监控

> 自动抓取网易 BUFF 上 **★ Karambit | Lore (Battle-Scarred)** 的最低在售价，
> 每天生成折线图；当价格超过你的购入价 ¥690 时，桌面弹窗提醒。

## 功能特性

- 每日定时（默认 20:00）抓取 BUFF 最低在售价
- 价格 > 目标价时 Windows 桌面 toast 弹窗（自带声音）
- 累计 30 天 BUFF 历史价格曲线作参考
- Vue 3 + ECharts 折线图（区分「每日抓取」与「BUFF 30 天均价」两条线）
- 盈亏金额 / 盈亏比例 / 监控天数 / 历史最低最高 一屏全览
- 所有数据本地 SQLite 存储，图表随数据自动增长
- 提醒去重：同一天同一目标价只弹一次窗

## 目录结构

```
csgo-price-tracker/
├── backend/
│   ├── main.py            # 一键启动入口（首次抓取 + 调度器 + API）
│   ├── app.py             # FastAPI 数据接口
│   ├── scheduler.py       # 每日定时任务
│   ├── scraper.py         # BUFF 接口抓取
│   ├── database.py        # SQLite 存储
│   ├── notifier.py        # 桌面弹窗
│   ├── config.json        # 配置（goods_id / 目标价 / 抓取时间…）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/Dashboard.vue
│   │   ├── components/{PriceChart,StatCard,AlertList}.vue
│   │   ├── stores/price.js
│   │   ├── api/index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── start-backend.bat      # 双击启动后端
├── start-frontend.bat     # 双击启动前端
└── README.md
```

## 快速开始（Windows）

### 1. 启动后端（抓取 + 调度 + API）

双击 `start-backend.bat`，首次运行会自动：

1. 创建 Python 虚拟环境 `backend\.venv`
2. 安装 `requests / fastapi / schedule / plyer / win10toast` 等依赖
3. 立即抓取一次当前价格
4. 注册每日 20:00 的抓取任务
5. 启动 API 服务（默认 http://127.0.0.1:8765）

保持该窗口开启，关闭窗口 = 停止监控。

### 2. 启动前端（折线图页面）

另开一个窗口，双击 `start-frontend.bat`，浏览器打开
[http://127.0.0.1:5173](http://127.0.0.1:5173) 即可看到折线图与所有指标。

> 不需要前端也能用：弹窗提醒、历史数据都已经在后端跑。

## 配置项（`backend/config.json`）

| 字段 | 含义 | 默认 |
| --- | --- | --- |
| `goods_id` | BUFF 物品 ID | `781593` |
| `item_name` | 物品显示名 | `★ Karambit \| Lore (Battle-Scarred) - 弯刀 传说 久经沙场` |
| `target_price` | 触发提醒的价格阈值 | `690.0` |
| `purchase_price` | 你的购入价（用于计算盈亏） | `690.0` |
| `check_time` | 每日抓取时间 | `20:00` |
| `api_host` / `api_port` | API 服务地址 | `127.0.0.1` / `8765` |
| `price_history_days` | 拉取 BUFF 历史价格的天数 | `30` |
| `request_interval_seconds` | 请求间隔（礼貌爬取） | `3` |
| `user_agent` | 自定义 UA | Chrome 120 |

### 怎么找自己的 `goods_id`？

打开 [buff.163.com](https://buff.163.com) → 搜索 **Karambit Lore Battle-Scarred**
→ 点进物品页 → 浏览器地址栏 URL 里 `goods_id=xxxxx` 那个数字就是。
把它写进 `config.json` 即可。

## 提醒方式

当前版本只内置了 **Windows 桌面 toast**，按下面的优先级尝试：

1. PowerShell 原生 `Windows.UI.Notifications`（无需额外安装）
2. `win10toast`（`pip install win10toast`）
3. `plyer` 跨平台通知

若三种都失败，请到 `notifier.py` 顶部加入你自己的推送实现
（飞书 / 钉钉 / 邮件 webhook 等），函数签名保持 `send_desktop_notification(title, message)`。

## API 速查

后端同时提供 REST 接口，前端就是消费这些接口：

- `GET  /api/config` — 当前配置
- `POST /api/config` — 修改配置（热更新）
- `GET  /api/price/latest` — 最新一次抓取结果
- `GET  /api/price/daily` — 本机累计的每日最低在售价
- `GET  /api/price/history` — BUFF 30 天均价历史
- `GET  /api/alerts` — 历史提醒记录
- `POST /api/check/now` — 立刻执行一次抓取（前端「立即抓取一次」按钮）

可视化文档：http://127.0.0.1:8765/docs

## 常见问题

**Q：弹窗没出现？**
A：先看终端有没有 `已触发提醒: ¥xxx > ¥690` 的日志。
   Windows 11/10 第一次会弹「是否允许此应用显示通知」，要点允许。
   也可以打开「设置 → 系统 → 通知」确认 PowerShell/终端在通知列表里。

**Q：抓取失败 `BUFF 返回错误: ...`？**
A：极少数情况下 BUFF 接口会校验登录态。可以稍后再试，
   或者在 `scraper.py` 的 session 头里加你自己的 BUFF cookie。

**Q：换物品怎么办？**
A：改 `config.json` 的 `goods_id` 和 `item_name`，重启后端即可。
   前端会自动按新 goods_id 查询。

**Q：怎么关掉监控？**
A：直接关掉后端窗口即可，定时任务随之结束。

## 许可

仅用于学习与个人交易参考，请勿高频请求 BUFF 接口。
