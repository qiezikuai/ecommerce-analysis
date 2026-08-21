# -*- coding: utf-8 -*-
"""Olist 真实数据 ETL：把 data/olist/raw/ 下 9 个 CSV 清洗后导入 MySQL。
- 库: ecommerce(沿用 v1 的 analyst 账号, 无建库权限), 表名加 olist_ 前缀
- v1 模拟数据的 user_behavior 表不受影响
- 清洗规则: 空值转 NULL, 时间列转 DATETIME, 数字列转数值类型
用法: python scripts/olist_import_to_mysql.py
"""
import os, time
import pandas as pd
import pymysql

sys_out = __import__("sys").stdout
try:
    sys_out.reconfigure(encoding="utf-8")
except Exception:
    pass

base = os.path.dirname(os.path.abspath(__file__))

def load_env(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d

cfg = load_env(os.path.join(base, "..", "config", "db.env"))
raw_dir = os.path.join(base, "..", "data", "olist", "raw")

# 表名 -> (csv 文件名, 列顺序)
# 数据集原始列的已知拼写错误 -> 标准列名 (ETL 标准化)
COLUMN_MAP = {
    "olist_products": {
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    },
}

TABLES = [
    ("olist_customers",                 "olist_customers_dataset.csv"),
    ("olist_geolocation",               "olist_geolocation_dataset.csv"),
    ("olist_orders",                    "olist_orders_dataset.csv"),
    ("olist_order_items",               "olist_order_items_dataset.csv"),
    ("olist_order_payments",            "olist_order_payments_dataset.csv"),
    ("olist_order_reviews",             "olist_order_reviews_dataset.csv"),
    ("olist_products",                  "olist_products_dataset.csv"),
    ("olist_sellers",                   "olist_sellers_dataset.csv"),
    ("olist_product_category_translation", "product_category_name_translation.csv"),
]

conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
                       password=cfg["password"], database=cfg["database"], charset="utf8mb4")
conn.autocommit(False)

# 1) 建表
with conn.cursor() as cur:
    ddl = open(os.path.join(base, "..", "sql", "olist", "01_建表.sql"), encoding="utf-8-sig").read()
    for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
        cur.execute(stmt)
conn.commit()
print("建表完成: ecommerce 库内 olist_* 共 9 张表")

# 2) 导入
def to_mysql_value(v):
    if pd.isna(v):
        return None
    return v

t0 = time.time()
for table, csv_name in TABLES:
    csv_path = os.path.join(raw_dir, csv_name)
    df = pd.read_csv(csv_path, dtype=str)
    if table in COLUMN_MAP:
        df = df.rename(columns=COLUMN_MAP[table])
    cols = list(df.columns)
    n = len(df)
    insert_sql = "INSERT INTO `%s` (%s) VALUES (%s)" % (
        table, ",".join("`%s`" % c for c in cols), ",".join(["%s"] * len(cols)))
    t1 = time.time()
    with conn.cursor() as cur:
        for i in range(0, n, 20000):
            chunk = df.iloc[i:i + 20000]
            rows = [tuple(to_mysql_value(v) for v in r) for r in chunk.itertuples(index=False)]
            cur.executemany(insert_sql, rows)
            conn.commit()
    print("导入 %-40s %8s 行  耗时 %.1fs" % (csv_name, format(n, ","), time.time() - t1), flush=True)

# 3) 核对
with conn.cursor() as cur:
    print("\n=== 核对 ===")
    for table, _ in TABLES:
        cur.execute("SELECT COUNT(*) FROM `%s`" % table)
        print("%-40s %s 行" % (table, format(cur.fetchone()[0], ",")))
    cur.execute("SELECT MIN(order_purchase_timestamp), MAX(order_purchase_timestamp) FROM olist_orders")
    print("订单时间范围:", cur.fetchone())
conn.close()
print("\nETL 完成, 总耗时 %.0fs" % (time.time() - t0))
