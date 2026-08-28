# DataPilot — 自然语言数据分析 Agent

用户输入自然语言问题（如"最近 30 天哪些商品销量下降最明显？主要原因可能是什么？"），
Agent 自动理解问题、选择工具、查询 MySQL、计算指标、生成分析结论。

## 技术栈

- Python 3.13（uv 管理）
- MySQL 8.4（Windows 服务 `MySQL84`，开机自启）
- pymysql + python-dotenv

## 数据库

连接配置见 `.env`（已就绪，勿提交到 git）：

```
host=127.0.0.1  port=3306  db=datapilot
user=datapilot  password=DataPilot@2026
```

服务管理（管理员终端）：`net start MySQL84` / `net stop MySQL84`
root 账号：`root / Root@DataPilot2026`（仅本机维护用）

### 表结构（9 张表，字段明细见 docs/database-guide.md，DDL 见 scripts/schema.sql）

| 表 | 说明 | 行数 |
|---|---|---|
| categories | 商品类目 | 8 |
| products | 商品（含当前售价/成本/上架日期） | 120 |
| customers | 客户（含省市/注册渠道） | 2,000 |
| promotions | 促销活动（时间范围+折扣+适用范围） | 4 |
| price_changes | 调价记录（旧价/新价/原因） | 3 |
| orders | 订单（2025-08-27 ~ 2026-08-26） | 57,392 |
| order_items | 订单明细（成交单价已含促销折扣） | 91,679 |
| product_daily_stats | 每日经营指标：浏览/加购/成交/退款/库存 | 42,916 |
| reviews | 商品评价（1-5 星 + 文本） | 9,982 |

## 假数据中埋的"剧情"（用于验证 Agent 归因能力）

1. **涨价导致下滑**：商品 5 / 23 / 41 于 2026-07-25 涨价 15%~28%，之后销量降约一半。
   线索表：`price_changes`。
2. **差评爆发**：商品 12 / 30 / 48 自 2026-08-01 起差评激增、评分下滑，转化下降。
   线索表：`reviews` + `product_daily_stats`（浏览量稳但成交降）。
3. **大促后回落（基数效应）**：类目"服饰鞋包"（category_id=4）2026-07-01~07-15 八折大促，
   销量冲高后回落，环比看"下降"但并非经营异常。线索表：`promotions`。
4. **断货**：商品 75 / 90 自 2026-08-10 起库存归零、销量归零。
   线索表：`product_daily_stats.stock_qty`。
5. **对照组**：商品 8 / 66 / 110 持续增长；新品 118 / 119 / 120（2026-06~07 上架）快速爬坡。
6. **全局节奏**：周末销量偏高、618 大促（06-01~06-20）全场 85 折、双 11、春节物流低谷。

## 常用命令

```bash
uv sync                                        # 同步依赖
uv run python scripts/seed_data.py --reset     # 重建表并重灌假数据（约 1 分钟）
```
