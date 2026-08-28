"""DataPilot 假数据生成器

生成一个带"剧情"的电商数据集，用于自然语言数据分析 Agent 开发：
- 商品A组：7月底涨价 -> 近30天销量明显下滑（价格因素）
- 商品B组：8月初差评爆发 -> 转化率下降（口碑因素）
- 商品C组：7月上旬大促爆量 -> 大促结束后环比"下滑"（基数效应）
- 商品D组：8月中旬断货 -> 销量归零（库存因素）
- 全局：618大促、周末效应、温和增长趋势、若干新品快速增长

用法:
    uv run python scripts/seed_data.py [--reset]
"""

import argparse
import datetime as dt
import random
from pathlib import Path

import pymysql
from dotenv import load_dotenv
import os

random.seed(42)

# ---------- 基础配置 ----------
START_DATE = dt.date(2025, 8, 27)
END_DATE = dt.date(2026, 8, 26)  # 昨天
NUM_DAYS = (END_DATE - START_DATE).days + 1

CATEGORIES = ["数码电子", "家用电器", "美妆个护", "服饰鞋包", "食品生鲜", "家居日用", "运动户外", "图书文娱"]

PRODUCT_TEMPLATES = {
    "数码电子": ["无线蓝牙耳机", "智能手表", "便携充电宝", "机械键盘", "4K运动相机", "降噪头戴耳机", "智能音箱", "电竞鼠标"],
    "家用电器": ["空气炸锅", "扫地机器人", "破壁机", "加湿器", "电热水壶", "挂烫机", "电动牙刷", "颈椎按摩仪"],
    "美妆个护": ["玻尿酸面膜", "氨基酸洁面", "防晒霜SPF50", "口红礼盒", "精华液", "洗发水套装", "电动剃须刀", "香水"],
    "服饰鞋包": ["纯棉T恤", "休闲运动鞋", "双肩包", "防晒衣", "牛仔裤", "棒球帽", "真丝衬衫", "帆布鞋"],
    "食品生鲜": ["每日坚果", "冷萃咖啡液", "全麦面包", "车厘子礼盒", "酸奶", "牛肉干", "燕麦片", "蜂蜜"],
    "家居日用": ["乳胶枕", "香薰蜡烛", "收纳箱套装", "保温杯", "四件套床品", "垃圾桶", "晾衣架", "桌面加湿器"],
    "运动户外": ["瑜伽垫", "登山杖", "速干衣", "露营帐篷", "筋膜枪", "骑行头盔", "跳绳", "运动水壶"],
    "图书文娱": ["科普图书套装", "儿童绘本", "手账本", "钢笔礼盒", "拼图1000片", "桌游", "书法字帖", "科幻小说"],
}

BRANDS = ["星辰", "极风", "蓝海", "云杉", "白鹭", "黑曜", "沐光", "山海", "初雪", "南屿", "拾光", "简致"]

SURNAMES = "王李张刘陈杨赵黄周吴徐孙马朱胡郭何林罗高郑梁谢宋唐许韩冯邓曹彭"
GIVEN_NAMES = ["伟", "芳", "娜", "敏", "静", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明", "超", "秀兰", "霞", "平", "刚", "桂英", "文", "辉", "力", "斌", "宇", "浩", "凯", "欣", "怡", "佳", "晨", "思远", "子涵", "雨欣", "一诺"]

PROVINCE_CITIES = [
    ("北京", ["北京"]), ("上海", ["上海"]), ("广东", ["广州", "深圳", "东莞", "佛山"]),
    ("浙江", ["杭州", "宁波", "温州"]), ("江苏", ["南京", "苏州", "无锡"]), ("四川", ["成都", "绵阳"]),
    ("湖北", ["武汉", "宜昌"]), ("湖南", ["长沙", "株洲"]), ("山东", ["济南", "青岛"]),
    ("福建", ["福州", "厦门"]), ("陕西", ["西安", "咸阳"]), ("重庆", ["重庆"]),
    ("河南", ["郑州", "洛阳"]), ("安徽", ["合肥", "芜湖"]), ("辽宁", ["沈阳", "大连"]),
]

CHANNELS = ["APP", "小程序", "网页", "线下门店"]
PAYMENTS = ["支付宝", "微信支付", "银行卡", "花呗分期"]

# 剧情分组（product id 从 1 开始，每类目 15 个，类目 c 的商品 id 范围 [(c-1)*15+1, c*15]）
PRICE_HIKE_IDS = [5, 23, 41]      # A组: 涨价 -> 销量下滑
BAD_REVIEW_IDS = [12, 30, 48]     # B组: 差评爆发
PROMO_CATEGORY_ID = 4             # C组所在类目（服饰鞋包）
PROMO_BASELINE_IDS = [47, 52, 58] # C组: 大促爆量后回落
STOCKOUT_IDS = [75, 90]           # D组: 断货
GROWING_IDS = [8, 66, 110]        # 对照组: 快速增长
NEW_PRODUCT_IDS = [118, 119, 120] # 新品（2026年6-7月上架）

PRICE_HIKE_DATE = dt.date(2026, 7, 25)
BAD_REVIEW_DATE = dt.date(2026, 8, 1)
STOCKOUT_DATE = dt.date(2026, 8, 10)

POSITIVE_REVIEWS = [
    "质量很好，超出预期，会回购！", "物流很快，包装严实，满意。", "性价比高，推荐给朋友了。",
    "用了一周才来评价，体验不错。", "颜值在线，功能也实用。", "老客户了，品质一如既往地稳。",
    "给家人买的，反馈说很好用。", "做工精细，这个价位很值。",
]
NEGATIVE_REVIEWS = [
    "用了两天就出问题，质量堪忧。", "和描述差距很大，失望。", "客服处理太慢，体验很差。",
    "做工粗糙，不值这个价。", "收到就是坏的，申请退款了。", "噪音太大，完全没法用。",
]


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def connect():
    load_dotenv()
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "datapilot"),
        password=os.getenv("DB_PASSWORD", "DataPilot@2026"),
        database=os.getenv("DB_NAME", "datapilot"),
        charset="utf8mb4",
        autocommit=False,
    )


def create_schema(cur, reset: bool):
    schema_path = Path(__file__).parent / "schema.sql"
    ddl = schema_path.read_text(encoding="utf-8")
    if reset:
        tables = ["reviews", "product_daily_stats", "order_items", "orders",
                  "price_changes", "promotions", "products", "customers", "categories"]
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for t in tables:
            cur.execute(f"DROP TABLE IF EXISTS {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)


def gen_dimensions(cur):
    # 类目
    cur.executemany("INSERT INTO categories (name) VALUES (%s)", [(c,) for c in CATEGORIES])

    # 商品
    products = []
    pid = 0
    for cat_id, cat in enumerate(CATEGORIES, start=1):
        for i in range(15):
            pid += 1
            base_name = PRODUCT_TEMPLATES[cat][i % len(PRODUCT_TEMPLATES[cat])]
            brand = random.choice(BRANDS)
            name = f"{brand} {base_name} {'Pro' if pid % 3 == 0 else 'S' if pid % 3 == 1 else ''}".strip()
            price = round(random.uniform(19, 2999), 2)
            if cat == "图书文娱":
                price = round(random.uniform(19, 199), 2)
            elif cat in ("数码电子", "家用电器"):
                price = round(random.uniform(99, 2999), 2)
            cost = round(price * random.uniform(0.35, 0.6), 2)
            if pid in NEW_PRODUCT_IDS:
                launch = dt.date(2026, 6, 1) + dt.timedelta(days=random.randint(0, 40))
            else:
                launch = START_DATE - dt.timedelta(days=random.randint(30, 600))
            products.append((cat_id, name, brand, price, cost, launch, "on_sale"))
    cur.executemany(
        "INSERT INTO products (category_id,name,brand,price,cost_price,launch_date,status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)", products)

    # 客户
    customers = []
    for _ in range(2000):
        province, cities = random.choice(PROVINCE_CITIES)
        reg = START_DATE - dt.timedelta(days=random.randint(0, 900))
        customers.append((
            random.choice(SURNAMES) + random.choice(GIVEN_NAMES),
            random.choice(["M", "F"]), province, random.choice(cities),
            random.choices(CHANNELS, weights=[45, 30, 15, 10])[0], reg,
        ))
    cur.executemany(
        "INSERT INTO customers (name,gender,province,city,channel,register_date) "
        "VALUES (%s,%s,%s,%s,%s,%s)", customers)

    # 促销活动
    promos = [
        ("618年中大促", dt.date(2026, 6, 1), dt.date(2026, 6, 20), 0.85, "all", None),
        ("夏季服饰狂欢节", dt.date(2026, 7, 1), dt.date(2026, 7, 15), 0.80, "category", PROMO_CATEGORY_ID),
        ("双11全球狂欢节", dt.date(2025, 11, 1), dt.date(2025, 11, 11), 0.82, "all", None),
        ("年货节", dt.date(2026, 1, 20), dt.date(2026, 2, 5), 0.88, "category", 5),
    ]
    cur.executemany(
        "INSERT INTO promotions (name,start_date,end_date,discount_rate,scope_type,scope_id) "
        "VALUES (%s,%s,%s,%s,%s,%s)", promos)

    # A组涨价记录
    price_rows = []
    for pid_ in PRICE_HIKE_IDS:
        cur.execute("SELECT price FROM products WHERE id=%s", (pid_,))
        old = float(cur.fetchone()[0])
        new = round(old * random.uniform(1.15, 1.28), 2)
        price_rows.append((pid_, PRICE_HIKE_DATE, old, new, "原材料成本上涨，调价"))
        cur.execute("UPDATE products SET price=%s WHERE id=%s", (new, pid_))
    cur.executemany(
        "INSERT INTO price_changes (product_id,change_date,old_price,new_price,reason) "
        "VALUES (%s,%s,%s,%s,%s)", price_rows)

    # 商品画像：基础日销量、转化率、促销敏感度
    profiles = {}
    for pid_ in range(1, 121):
        base = random.uniform(0.4, 3.2)
        if random.random() < 0.08:
            base = random.uniform(4.0, 8.0)  # 少数爆款
        if pid_ in NEW_PRODUCT_IDS:
            base = 0.0
        profiles[pid_] = {
            "base": base,
            "conv": random.uniform(0.02, 0.05),       # 成交转化率
            "promo_lift": random.uniform(1.5, 3.0),   # 大促提升系数
        }
    return profiles


def active_promos(cur):
    cur.execute("SELECT start_date,end_date,discount_rate,scope_type,scope_id FROM promotions")
    return cur.fetchall()


def day_multiplier(d: dt.date) -> float:
    """全局日系数：趋势 + 周末 + 618 氛围"""
    idx = (d - START_DATE).days
    m = 1.0 + 0.15 * idx / NUM_DAYS                       # 温和增长
    if d.weekday() >= 5:
        m *= 1.25                                          # 周末
    if dt.date(2026, 6, 1) <= d <= dt.date(2026, 6, 20):
        m *= 1.6                                           # 618 氛围（具体折扣由促销表体现）
    if dt.date(2026, 2, 15) <= d <= dt.date(2026, 2, 22):
        m *= 0.7                                           # 春节物流停运低谷
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="先删除所有表再重建")
    args = parser.parse_args()

    conn = connect()
    cur = conn.cursor()

    create_schema(cur, reset=args.reset)
    conn.commit()
    print("[1/6] 表结构就绪")

    profiles = gen_dimensions(cur)
    conn.commit()
    print("[2/6] 维度数据: 8 类目 / 120 商品 / 2000 客户 / 4 促销活动")

    promos = active_promos(cur)
    cur.execute("SELECT id, category_id, launch_date, price FROM products")
    pmeta = {r[0]: {"cat": r[1], "launch": r[2], "price": float(r[3])} for r in cur.fetchall()}

    # A组涨价前的旧价
    cur.execute("SELECT product_id, old_price FROM price_changes")
    old_prices = {r[0]: float(r[1]) for r in cur.fetchall()}

    # ---------- 生成每日销量计划 ----------
    # daily_items[date] = list of (product_id, qty)；同时累计统计
    daily_items = {d: [] for d in daterange(START_DATE, END_DATE)}
    stats = {}   # (pid, date) -> dict(orders, amount, refunds)
    baseline_sold = {}  # (pid, date) -> 未受剧情影响的基准销量（推浏览量用）

    promo_windows = [(s, e, float(rate), st, sid) for (s, e, rate, st, sid) in promos]

    def promo_rate(pid_, cat, d):
        """返回该商品在 d 当天生效的促销折扣率，无促销返回 None"""
        for (s, e, rate, st, sid) in promo_windows:
            if s <= d <= e and (st == "all" or (st == "category" and sid == cat)
                                or (st == "product" and sid == pid_)):
                return rate
        return None

    for d in daterange(START_DATE, END_DATE):
        gm = day_multiplier(d)
        for pid_ in range(1, 121):
            meta = pmeta[pid_]
            if d < meta["launch"]:
                continue
            prof = profiles[pid_]
            base = prof["base"]
            if pid_ in NEW_PRODUCT_IDS:
                age = (d - meta["launch"]).days
                base = min(6.0, 0.3 + age * 0.15)  # 新品爬坡

            m = gm * random.uniform(0.75, 1.25)

            # 促销加成（618/双11 全场 + 类目活动）
            if promo_rate(pid_, meta["cat"], d) is not None:
                m *= prof["promo_lift"]

            baseline = base * m
            baseline_sold[(pid_, d)] = baseline
            actual = baseline

            # ---- 剧情修正 ----
            if pid_ in PRICE_HIKE_IDS and d >= PRICE_HIKE_DATE:
                actual *= 0.45                       # 涨价后需求萎缩
            if pid_ in BAD_REVIEW_IDS and d >= BAD_REVIEW_DATE:
                actual *= 0.5                        # 差评压制转化
            if pid_ in STOCKOUT_IDS and d >= STOCKOUT_DATE:
                actual = 0.0                         # 断货
            if pid_ in GROWING_IDS and d >= dt.date(2026, 5, 1):
                actual *= 1.0 + min(1.2, (d - dt.date(2026, 5, 1)).days * 0.015)  # 持续增长

            frac = actual - int(actual)
            qty = int(actual) + (1 if random.random() < frac else 0)
            qty = max(0, qty)
            if qty == 0:
                continue
            # 拆成 1~3 件的购买实例
            remaining = qty
            while remaining > 0:
                take = min(remaining, random.choices([1, 2, 3], weights=[70, 22, 8])[0])
                daily_items[d].append((pid_, take))
                remaining -= take
            stats.setdefault((pid_, d), {"orders": 0, "amount": 0.0, "refunds": 0})
            stats[(pid_, d)]["orders"] += qty

    print(f"[3/6] 销量计划生成完毕: {sum(len(v) for v in daily_items.values())} 条购买记录")

    # ---------- 生成订单 ----------
    cur.execute("SELECT id FROM customers")
    cust_ids = [r[0] for r in cur.fetchall()]
    cust_weights = [random.uniform(0.3, 1.0) for _ in cust_ids]

    all_orders = []    # (order_no, customer_id, order_time, status, payment, total, n_items)
    all_items = []     # (order_idx, product_id, quantity, unit_price, discount)
    order_idx = 0

    for d in daterange(START_DATE, END_DATE):
        items_today = daily_items[d]
        random.shuffle(items_today)
        i = 0
        while i < len(items_today):
            n = random.choices([1, 2, 3], weights=[55, 30, 15])[0]
            chunk = items_today[i:i + n]
            i += n
            cust = random.choices(cust_ids, weights=cust_weights)[0]
            hour = random.choices(range(24), weights=[1,1,1,1,1,2,3,4,5,6,7,8,9,9,8,7,7,8,9,10,10,8,5,2])[0]
            otime = dt.datetime(d.year, d.month, d.day, hour, random.randint(0, 59), random.randint(0, 59))
            status = random.choices(["completed", "refunded", "cancelled"], weights=[92, 5, 3])[0]

            total = 0.0
            for (pid_, qty) in chunk:
                meta = pmeta[pid_]
                # 当天生效价格（涨价前用旧价）
                price = old_prices[pid_] if (pid_ in old_prices and d < PRICE_HIKE_DATE) else meta["price"]
                rate = promo_rate(pid_, meta["cat"], d)
                if rate is not None:
                    unit = round(price * rate, 2)
                    disc = round((price - unit) * qty, 2)
                else:
                    unit, disc = round(price, 2), 0.0
                all_items.append((order_idx, pid_, qty, unit, disc))
                total += unit * qty
                if status == "completed":
                    key = (pid_, d)
                    if key in stats:
                        stats[key]["amount"] += unit * qty
                        if random.random() < 0.03:
                            stats[key]["refunds"] += qty
            all_orders.append((cust, otime, status, random.choice(PAYMENTS), round(total, 2)))
            order_idx += 1

    print(f"[4/6] 订单生成完毕: {len(all_orders)} 单 / {len(all_items)} 条明细，开始写入...")

    # 分批写入订单，记录 ID 区间
    order_ids = []
    BATCH = 2000
    for b in range(0, len(all_orders), BATCH):
        rows = all_orders[b:b + BATCH]
        values = []
        for k, (cust, otime, status, pay, total) in enumerate(rows):
            ono = f"DP{otime.strftime('%Y%m%d')}{b + k + 1:08d}"
            values.append((ono, cust, otime, status, pay, total))
        cur.executemany(
            "INSERT INTO orders (order_no,customer_id,order_time,status,payment_method,total_amount) "
            "VALUES (%s,%s,%s,%s,%s,%s)", values)
        first = cur.lastrowid
        conn.commit()
        order_ids.extend(range(first, first + len(rows)))

    item_rows = [(order_ids[oi], pid_, qty, unit, disc) for (oi, pid_, qty, unit, disc) in all_items]
    for b in range(0, len(item_rows), BATCH):
        cur.executemany(
            "INSERT INTO order_items (order_id,product_id,quantity,unit_price,discount_amount) "
            "VALUES (%s,%s,%s,%s,%s)", item_rows[b:b + BATCH])
        conn.commit()

    # ---------- 每日经营指标 ----------
    stock = {pid_: random.randint(300, 800) for pid_ in range(1, 121)}
    stat_rows = []
    for d in daterange(START_DATE, END_DATE):
        for pid_ in range(1, 121):
            if d < pmeta[pid_]["launch"]:
                continue
            st = stats.get((pid_, d))
            sold = st["orders"] if st else 0
            amount = round(st["amount"], 2) if st else 0.0
            refunds = st["refunds"] if st else 0

            base_sold = baseline_sold.get((pid_, d), 0.0)
            views = int(base_sold / profiles[pid_]["conv"] * random.uniform(0.85, 1.15))
            if pid_ in STOCKOUT_IDS and d >= STOCKOUT_DATE:
                views = int(views * 0.5)   # 断货后曝光下降
            cart = int(views * random.uniform(0.05, 0.10))

            if pid_ in STOCKOUT_IDS and d >= STOCKOUT_DATE:
                stock[pid_] = 0
            else:
                stock[pid_] = max(0, stock[pid_] - sold)
                if stock[pid_] < 50:
                    stock[pid_] += random.randint(400, 700)

            stat_rows.append((pid_, d, views, cart, sold, amount, refunds, stock[pid_]))

    for b in range(0, len(stat_rows), BATCH):
        cur.executemany(
            "INSERT INTO product_daily_stats (product_id,stat_date,views,cart_adds,orders_count,"
            "sales_amount,refund_count,stock_qty) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            stat_rows[b:b + BATCH])
        conn.commit()
    print(f"[5/6] 每日指标写入完毕: {len(stat_rows)} 行")

    # ---------- 评价 ----------
    review_rows = []
    for (oi, pid_, qty, unit, disc) in all_items:
        if random.random() > 0.12:
            continue
        cust, otime, status = all_orders[oi][0], all_orders[oi][1], all_orders[oi][2]
        if status != "completed":
            continue
        rtime = otime + dt.timedelta(days=random.randint(1, 10), minutes=random.randint(0, 600))
        if rtime.date() > END_DATE:
            continue
        if pid_ in BAD_REVIEW_IDS and rtime.date() >= BAD_REVIEW_DATE:
            rating = random.choices([1, 2, 3, 4, 5], weights=[35, 30, 15, 10, 10])[0]
            content = random.choice(NEGATIVE_REVIEWS if rating <= 2 else POSITIVE_REVIEWS)
        else:
            rating = random.choices([1, 2, 3, 4, 5], weights=[2, 3, 8, 30, 57])[0]
            content = random.choice(POSITIVE_REVIEWS if rating >= 4 else NEGATIVE_REVIEWS)
        review_rows.append((pid_, cust, rating, content, rtime))

    for b in range(0, len(review_rows), BATCH):
        cur.executemany(
            "INSERT INTO reviews (product_id,customer_id,rating,content,review_time) "
            "VALUES (%s,%s,%s,%s,%s)", review_rows[b:b + BATCH])
        conn.commit()
    print(f"[6/6] 评价写入完毕: {len(review_rows)} 条")

    cur.execute("SELECT COUNT(*) FROM orders")
    print(f"\n完成! orders={cur.fetchone()[0]}", end=" ")
    cur.execute("SELECT COUNT(*) FROM order_items")
    print(f"order_items={cur.fetchone()[0]}", end=" ")
    cur.execute("SELECT COUNT(*) FROM product_daily_stats")
    print(f"daily_stats={cur.fetchone()[0]}")
    conn.close()


if __name__ == "__main__":
    main()
