# DataPilot 数据库设计文档

> 本文档由线上库 `information_schema` 实际导出整理，与运行中的 MySQL 完全一致。
> 数据库：MySQL 8.4.9（Windows 服务 `MySQL84`）｜字符集：utf8mb4 ｜ 数据时间范围：2025-08-27 ~ 2026-08-26

---

## 一、连接方式

### 1.1 连接参数

| 参数 | 值 | 说明 |
|---|---|---|
| Host | `127.0.0.1` | 本机回环 |
| Port | `3306` | 默认端口 |
| Database | `datapilot` | 业务库名 |
| User | `datapilot` | 应用账号，仅授权 datapilot 库 |
| Password | `DataPilot@2026` | — |
| 字符集 | `utf8mb4` | 客户端连接时必须指定，否则中文乱码 |

维护用 root 账号：`root / Root@DataPilot2026`（仅本机维护使用，不要写进应用代码）。

服务管理（管理员终端）：`net start MySQL84` / `net stop MySQL84`（开机自启）。

### 1.2 项目内 .env（已配置）

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=datapilot
DB_PASSWORD=DataPilot@2026
DB_NAME=datapilot
```

### 1.3 Python（pymysql）连接示例

```python
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    charset="utf8mb4",
)
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM orders")
    print(cur.fetchone())
conn.close()
```

### 1.4 命令行连接

```bash
mysql -h 127.0.0.1 -P 3306 -u datapilot -p datapilot --default-character-set=utf8mb4
# 密码: DataPilot@2026
```

### 1.5 JDBC URL（PyCharm / DBeaver 等客户端通用）

```
jdbc:mysql://127.0.0.1:3306/datapilot?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
```

---

## 二、表清单与关系

共 **9 张表**，电商销售分析场景。

| 表名 | 说明 | 行数 | 主键 |
|---|---|---|---|
| categories | 商品类目表 | 8 | id |
| products | 商品表 | 120 | id |
| customers | 客户表 | 2,000 | id |
| promotions | 促销活动表 | 4 | id |
| price_changes | 商品调价记录表 | 3 | id |
| orders | 订单表 | 57,392 | id（order_no 唯一） |
| order_items | 订单明细表 | 91,679 | id |
| product_daily_stats | 商品每日经营指标表 | 42,916 | (product_id, stat_date) |
| reviews | 商品评价表 | 9,982 | id |

### 关系（外键 / 逻辑关联）

```
categories 1──N products            （外键 fk_products_category）
products   1──N order_items         （外键 fk_items_product）
orders     1──N order_items         （外键 fk_items_order）
customers  1──N orders              （逻辑关联 orders.customer_id）
customers  1──N reviews             （逻辑关联 reviews.customer_id）
products   1──N price_changes       （逻辑关联）
products   1──N product_daily_stats （逻辑关联，stats 以 (product_id,stat_date) 为主键）
promotions 通过 scope_type/scope_id 逻辑关联 categories 或 products
```

---

## 三、表结构明细

### 3.1 categories — 商品类目表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | int | NOT NULL | PRI, 自增 | — | 类目ID |
| name | varchar(50) | NOT NULL | — | — | 类目名称 |
| created_at | datetime | NULL | — | CURRENT_TIMESTAMP | 创建时间 |

现有类目：数码电子、家用电器、美妆个护、服饰鞋包、食品生鲜、家居日用、运动户外、图书文娱（id 1~8）。

### 3.2 products — 商品表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | int | NOT NULL | PRI, 自增 | — | 商品ID |
| category_id | int | NOT NULL | MUL（idx_category） | — | 所属类目 → categories.id |
| name | varchar(100) | NOT NULL | — | — | 商品名称 |
| brand | varchar(50) | NOT NULL | — | — | 品牌 |
| price | decimal(10,2) | NOT NULL | — | — | 当前售价 |
| cost_price | decimal(10,2) | NOT NULL | — | — | 成本价 |
| launch_date | date | NOT NULL | — | — | 上架日期 |
| status | enum('on_sale','off_sale') | NULL | — | on_sale | 销售状态 |
| created_at | datetime | NULL | — | CURRENT_TIMESTAMP | 创建时间 |

外键：`fk_products_category (category_id) → categories(id)`。
注意：`price` 是**当前**售价；历史价格见 price_changes。

### 3.3 customers — 客户表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | int | NOT NULL | PRI, 自增 | — | 客户ID |
| name | varchar(50) | NOT NULL | — | — | 客户姓名 |
| gender | enum('M','F') | NULL | — | — | 性别 |
| province | varchar(30) | NULL | MUL（idx_region 前缀） | — | 省份 |
| city | varchar(30) | NULL | — | — | 城市 |
| channel | varchar(20) | NULL | — | — | 注册渠道：APP/小程序/网页/线下门店 |
| register_date | date | NULL | — | — | 注册日期 |

索引：`idx_region (province, city)`。

### 3.4 promotions — 促销活动表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | int | NOT NULL | PRI, 自增 | — | 活动ID |
| name | varchar(100) | NOT NULL | — | — | 活动名称 |
| start_date | date | NOT NULL | MUL（idx_dates） | — | 开始日期 |
| end_date | date | NOT NULL | — | — | 结束日期 |
| discount_rate | decimal(4,2) | NOT NULL | — | — | 折扣率，0.85 = 85折 |
| scope_type | enum('all','category','product') | NOT NULL | — | — | 适用范围 |
| scope_id | int | NULL | — | — | category 时为类目ID，product 时为商品ID，all 时为 NULL |

现有活动：618 年中大促（全场 85 折）、夏季服饰狂欢节（服饰鞋包 8 折）、双 11（全场 82 折）、年货节（食品生鲜 88 折）。

### 3.5 price_changes — 商品调价记录表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | int | NOT NULL | PRI, 自增 | — | 记录ID |
| product_id | int | NOT NULL | MUL（idx_product） | — | 商品ID |
| change_date | date | NOT NULL | MUL（idx_date） | — | 调价日期 |
| old_price | decimal(10,2) | NOT NULL | — | — | 调前价 |
| new_price | decimal(10,2) | NOT NULL | — | — | 调后价 |
| reason | varchar(100) | NULL | — | — | 调价原因 |

### 3.6 orders — 订单表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | bigint | NOT NULL | PRI, 自增 | — | 订单ID |
| order_no | varchar(32) | NOT NULL | UNI | — | 订单号，格式 DP+日期+序号 |
| customer_id | int | NOT NULL | MUL（idx_customer） | — | 下单客户 → customers.id |
| order_time | datetime | NOT NULL | MUL（idx_order_time） | — | 下单时间 |
| status | enum('completed','refunded','cancelled') | NULL | MUL（idx_status） | completed | 订单状态 |
| payment_method | varchar(20) | NULL | — | — | 支付方式：支付宝/微信支付/银行卡/花呗分期 |
| total_amount | decimal(12,2) | NOT NULL | — | — | 实付金额 |

**口径**：统计销售额/销量时一般只取 `status='completed'`。

### 3.7 order_items — 订单明细表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | bigint | NOT NULL | PRI, 自增 | — | 明细ID |
| order_id | bigint | NOT NULL | MUL（idx_order） | — | 订单ID → orders.id |
| product_id | int | NOT NULL | MUL（idx_product） | — | 商品ID → products.id |
| quantity | int | NOT NULL | — | — | 购买数量 |
| unit_price | decimal(10,2) | NOT NULL | — | — | 成交单价（**已含促销折扣**） |
| discount_amount | decimal(10,2) | NULL | — | 0.00 | 优惠金额 |

外键：`fk_items_order → orders(id)`、`fk_items_product → products(id)`。

### 3.8 product_daily_stats — 商品每日经营指标表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| product_id | int | NOT NULL | PRI(联合) | — | 商品ID |
| stat_date | date | NOT NULL | PRI(联合), MUL（idx_date） | — | 统计日期 |
| views | int | NULL | — | 0 | 浏览量 |
| cart_adds | int | NULL | — | 0 | 加购次数 |
| orders_count | int | NULL | — | 0 | 成交件数 |
| sales_amount | decimal(12,2) | NULL | — | 0.00 | 销售额 |
| refund_count | int | NULL | — | 0 | 退款件数 |
| stock_qty | int | NULL | — | 0 | 当日库存 |

用途：转化漏斗（views → cart_adds → orders_count）与库存分析，是"归因"类问题的核心表。

### 3.9 reviews — 商品评价表

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | bigint | NOT NULL | PRI, 自增 | — | 评价ID |
| product_id | int | NOT NULL | MUL（idx_product） | — | 商品ID |
| customer_id | int | NOT NULL | — | — | 评价客户 |
| rating | tinyint | NOT NULL | MUL（idx_rating） | — | 评分 1-5 |
| content | varchar(500) | NULL | — | — | 评价内容 |
| review_time | datetime | NOT NULL | MUL（idx_time） | — | 评价时间 |

---

## 四、数据中的"剧情"（供 Agent 归因验证）

假数据不是纯随机的，埋了可被 SQL 查出的因果关系，用来检验 Agent 的分析结论是否正确：

1. **涨价导致下滑**：商品 5 / 23 / 41 于 2026-07-25 涨价 15%~28%（price_changes 有记录），之后销量降约一半。
2. **差评爆发**：商品 12 / 30 / 48 自 2026-08-01 起 reviews 中 1-2 星占比骤升、均分下滑；product_daily_stats 表现为浏览量稳定但成交下降（转化问题）。
3. **大促后回落（基数效应）**：类目"服饰鞋包"（category_id=4）在 2026-07-01~07-15 八折大促期间销量冲高，结束后环比"下滑"，属正常回落而非经营异常（promotions 有记录）。
4. **断货**：商品 75 / 90 自 2026-08-10 起 stock_qty=0、销量归零。
5. **对照组**：商品 8 / 66 / 110 持续增长；新品 118 / 119 / 120 于 2026-06~07 上架、快速爬坡。
6. **全局节奏**：周末销量偏高、618（06-01~06-20）全场 85 折、双 11、春节物流低谷（2 月中旬）。

---

## 五、常用查询示例

### 5.1 最近 30 天销量 Top 商品

```sql
SELECT p.name, SUM(oi.quantity) AS sold
FROM order_items oi
JOIN orders o  ON o.id = oi.order_id AND o.status = 'completed'
JOIN products p ON p.id = oi.product_id
WHERE o.order_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.id, p.name
ORDER BY sold DESC
LIMIT 10;
```

### 5.2 环比下滑最明显的商品（示例问题的核心查询）

```sql
SELECT p.id, p.name,
       SUM(o.order_time >= '2026-07-28') AS last30,
       SUM(o.order_time BETWEEN '2026-06-28' AND '2026-07-27') AS prev30
FROM order_items oi
JOIN orders o  ON o.id = oi.order_id AND o.status = 'completed'
JOIN products p ON p.id = oi.product_id
GROUP BY p.id, p.name
HAVING prev30 > 20
ORDER BY (last30 - prev30) / prev30 ASC
LIMIT 10;
```

### 5.3 某商品的转化漏斗（近 30 天）

```sql
SELECT SUM(views) AS views, SUM(cart_adds) AS carts, SUM(orders_count) AS sold,
       ROUND(SUM(orders_count) / NULLIF(SUM(views), 0), 4) AS cvr
FROM product_daily_stats
WHERE product_id = 48
  AND stat_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

### 5.4 某商品评分趋势（差评排查）

```sql
SELECT DATE_FORMAT(review_time, '%Y-%m') AS month,
       COUNT(*) AS cnt, ROUND(AVG(rating), 2) AS avg_rating
FROM reviews
WHERE product_id = 48
GROUP BY month ORDER BY month;
```

---

## 六、维护与重灌

```bash
# 重建全部表并重灌假数据（约 1 分钟，随机种子固定可复现）
cd D:\DataPilot
uv run python scripts/seed_data.py --reset

# 服务管理（管理员终端）
net stop MySQL84
net start MySQL84
```

相关文件：`scripts/schema.sql`（建表 DDL）、`scripts/seed_data.py`（数据生成器）、`.env`（连接配置）。
