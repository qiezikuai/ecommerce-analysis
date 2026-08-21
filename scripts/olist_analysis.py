# -*- coding: utf-8 -*-
"""Olist 真实数据 Python 分析：读 MySQL -> 导出 CSV -> 生成图表。
产出: report/exports_olist/*.csv, report/charts_olist/*.png
"""
import os, sys
import pandas as pd
import numpy as np
import pymysql
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.stdout.reconfigure(encoding="utf-8")
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(base, ".."))

# 中文字体
_avail = {x.name for x in font_manager.fontManager.ttflist}
_font = next((f for f in ["Microsoft YaHei", "SimHei", "msyh"] if f in _avail), None)
if _font:
    plt.rcParams["font.sans-serif"] = [_font]
plt.rcParams["axes.unicode_minus"] = False

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

cfg = load_env(os.path.join(root, "config", "db.env"))
conn = pymysql.connect(host=cfg["host"], port=int(cfg["port"]), user=cfg["user"],
                       password=cfg["password"], database=cfg["database"], charset="utf8mb4")
EX = os.path.join(root, "report", "exports_olist")
CH = os.path.join(root, "report", "charts_olist")
os.makedirs(EX, exist_ok=True); os.makedirs(CH, exist_ok=True)

def q(sql):
    return pd.read_sql(sql, conn)

# ---------- 1. 订单状态漏斗 ----------
funnel = q("""
SELECT '下单' AS stage, COUNT(*) AS cnt FROM olist_orders
UNION ALL SELECT '付款批准', COUNT(*) FROM olist_orders WHERE order_approved_at IS NOT NULL
UNION ALL SELECT '已发货', COUNT(*) FROM olist_orders WHERE order_delivered_carrier_date IS NOT NULL
UNION ALL SELECT '已送达', COUNT(*) FROM olist_orders WHERE order_delivered_customer_date IS NOT NULL
UNION ALL SELECT '已取消', COUNT(*) FROM olist_orders WHERE order_status='canceled'
""")
funnel = funnel.rename(columns={"stage": "阶段", "cnt": "订单数"})
funnel.to_csv(os.path.join(EX, "funnel.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(8, 5))
stages = funnel["阶段"].tolist(); cnts = funnel["订单数"].tolist()
colors = ["#4C72B0", "#55A868", "#DD8452", "#C44E52", "#8172B3"]
bars = ax.barh(stages[::-1], cnts[::-1], color=colors[::-1])
for b, c in zip(bars, cnts[::-1]):
    ax.text(b.get_width() + 1500, b.get_y() + b.get_height()/2, f"{c:,}", va="center", fontsize=10)
ax.set_xlabel("订单数"); ax.set_title("Olist 订单状态漏斗（下单→付款→发货→送达 / 取消）")
ax.set_xlim(0, max(cnts) * 1.12)
plt.tight_layout(); plt.savefig(os.path.join(CH, "01_订单状态漏斗.png"), dpi=150); plt.close()

# ---------- 2. 月度 GMV 与订单 ----------
monthly = q("""
SELECT DATE_FORMAT(o.order_purchase_timestamp,'%Y-%m') AS ym,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(p.payment_value),2) AS gmv
FROM olist_orders o LEFT JOIN olist_order_payments p ON o.order_id=p.order_id
GROUP BY ym ORDER BY ym
""")
monthly.to_csv(os.path.join(EX, "monthly.csv"), index=False, encoding="utf-8-sig")
m2 = monthly[monthly["orders"] >= 100]  # 去掉 2016 与 2018-09/10 的残缺月份
fig, ax = plt.subplots(figsize=(12, 5))
x = np.arange(len(m2))
ax.bar(x, m2["orders"], color="#4C72B0", label="订单数")
ax.set_ylabel("订单数")
ax2 = ax.twinx()
ax2.plot(x, m2["gmv"], color="#C44E52", marker="o", label="GMV(BRL)")
ax2.set_ylabel("GMV (BRL)")
ax.set_xticks(x); ax.set_xticklabels(m2["ym"], rotation=45, ha="right")
ax.set_title("月度订单数与 GMV（2017-01 ~ 2018-08，黑五 2017-11 为峰值）")
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))
plt.tight_layout(); plt.savefig(os.path.join(CH, "02_月度GMV与订单.png"), dpi=150); plt.close()

# ---------- 3. 支付方式 ----------
payment = q("""
SELECT payment_type AS pt, COUNT(*) AS cnt, ROUND(SUM(payment_value),2) AS amount
FROM olist_order_payments GROUP BY payment_type ORDER BY amount DESC
""")
payment.to_csv(os.path.join(EX, "payment.csv"), index=False, encoding="utf-8-sig")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
ax1.pie(payment["amount"], labels=payment["pt"], autopct="%.1f%%", startangle=90,
        colors=["#4C72B0", "#55A868", "#DD8452", "#C44E52", "#8172B3"])
ax1.set_title("支付方式金额占比")
ax2.bar(payment["pt"], payment["amount"], color="#4C72B0")
ax2.set_title("支付方式金额 (BRL)"); ax2.tick_params(axis="x", rotation=20)
plt.tight_layout(); plt.savefig(os.path.join(CH, "03_支付方式.png"), dpi=150); plt.close()

# ---------- 4. 时间规律：小时 / 星期 ----------
hour = q("SELECT HOUR(order_purchase_timestamp) AS h, COUNT(*) AS cnt FROM olist_orders GROUP BY h ORDER BY h")
weekday = q("SELECT DAYOFWEEK(order_purchase_timestamp) AS d, COUNT(*) AS cnt FROM olist_orders GROUP BY d ORDER BY d")
hour.to_csv(os.path.join(EX, "hourly.csv"), index=False, encoding="utf-8-sig")
weekday.to_csv(os.path.join(EX, "weekday.csv"), index=False, encoding="utf-8-sig")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
ax1.bar(hour["h"], hour["cnt"], color="#55A868")
ax1.set_title("下单小时分布"); ax1.set_xlabel("小时"); ax1.set_ylabel("订单数")
wd_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
ax2.bar([wd_names[d-1] for d in weekday["d"]], weekday["cnt"], color="#DD8452")
ax2.set_title("下单星期分布"); ax2.set_ylabel("订单数")
plt.tight_layout(); plt.savefig(os.path.join(CH, "04_时间规律.png"), dpi=150); plt.close()

# ---------- 5. R×M 价值矩阵 ----------
rm = q("""
WITH cus AS (
    SELECT c.customer_unique_id AS cid,
           DATEDIFF((SELECT MAX(order_purchase_timestamp) FROM olist_orders), MAX(o.order_purchase_timestamp)) AS R,
           COALESCE(SUM(p.payment_value),0) AS M
    FROM olist_orders o JOIN olist_customers c ON o.customer_id=c.customer_id
    LEFT JOIN olist_order_payments p ON o.order_id=p.order_id
    GROUP BY c.customer_unique_id
), tiered AS (
    SELECT cid, R, M,
           NTILE(3) OVER (ORDER BY M DESC) AS m_tier,
           NTILE(3) OVER (ORDER BY R ASC)  AS r_tier
    FROM cus
)
SELECT r_tier, m_tier, COUNT(*) AS n, ROUND(SUM(M),2) AS gmv, ROUND(AVG(M),2) AS aov
FROM tiered GROUP BY r_tier, m_tier ORDER BY r_tier, m_tier
""")
rm["r_label"] = rm["r_tier"].map({1: "R近", 2: "R中", 3: "R远"})
rm["m_label"] = rm["m_tier"].map({1: "M高", 2: "M中", 3: "M低"})
rm["gmv_share"] = (rm["gmv"] / rm["gmv"].sum() * 100).round(2)
rm.to_csv(os.path.join(EX, "rm_matrix.csv"), index=False, encoding="utf-8-sig")
pivot = rm.pivot(index="r_tier", columns="m_tier", values="n").reindex(index=[1, 2, 3], columns=[1, 2, 3])
fig, ax = plt.subplots(figsize=(7, 5.5))
im = ax.imshow(pivot.values, cmap="YlOrRd")
ax.set_xticks(range(3)); ax.set_yticks(range(3))
ax.set_xticklabels(["M高", "M中", "M低"]); ax.set_yticklabels(["R近", "R中", "R远"])
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{pivot.values[i,j]:,}", ha="center", va="center", fontsize=12)
ax.set_title("R×M 价值矩阵：客户数（近/中/远 × 高/中/低）")
plt.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout(); plt.savefig(os.path.join(CH, "05_RM价值矩阵.png"), dpi=150); plt.close()

# ---------- 6. 复购分布 ----------
fd = q("""
WITH cus AS (
    SELECT c.customer_unique_id AS cid, COUNT(DISTINCT o.order_id) AS f
    FROM olist_orders o JOIN olist_customers c ON o.customer_id=c.customer_id
    GROUP BY c.customer_unique_id
)
SELECT f, COUNT(*) AS n FROM cus GROUP BY f ORDER BY f
""")
fd = fd.rename(columns={"f": "购买次数", "n": "客户数"})
fd.to_csv(os.path.join(EX, "repurchase.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(fd["购买次数"].astype(str), fd["客户数"], color="#4C72B0")
ax.set_xlabel("购买次数"); ax.set_ylabel("客户数")
ax.set_title("客户购买次数分布：96.9% 仅购买 1 次（复购率 3.1%）")
for i, (x, y) in enumerate(zip(fd["购买次数"].astype(str), fd["客户数"])):
    ax.text(i, y + 800, f"{y:,}", ha="center", fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(CH, "06_复购分布.png"), dpi=150); plt.close()

# ---------- 7. 留存热力图 ----------
ret = q("""
WITH base AS (
    SELECT c.customer_unique_id AS cid,
           DATE_FORMAT(MIN(o.order_purchase_timestamp),'%Y-%m') AS cm,
           DATE_FORMAT(o.order_purchase_timestamp,'%Y-%m') AS bm
    FROM olist_orders o JOIN olist_customers c ON o.customer_id=c.customer_id
    GROUP BY c.customer_unique_id, DATE_FORMAT(o.order_purchase_timestamp,'%Y-%m')
)
SELECT cm AS cohort, TIMESTAMPDIFF(MONTH, CONCAT(cm,'-01'), CONCAT(bm,'-01')) AS mo,
       COUNT(DISTINCT cid) AS n
FROM base GROUP BY cm, mo ORDER BY cm, mo
""")
cohort_size = ret[ret["mo"] == 0].set_index("cohort")["n"]
ret["rate"] = ret.apply(lambda r: (r["n"] / cohort_size[r["cohort"]] * 100) if r["cohort"] in cohort_size.index else np.nan, axis=1)
ret["rate"] = ret["rate"].round(2)
ret.to_csv(os.path.join(EX, "retention.csv"), index=False, encoding="utf-8-sig")
piv = ret.pivot(index="cohort", columns="mo", values="rate")
piv = piv.loc[[c for c in piv.index if cohort_size.get(c, 0) >= 100]]
piv = piv[[c for c in piv.columns if c <= 12]]
fig, ax = plt.subplots(figsize=(11, 6))
im = ax.imshow(piv.values, cmap="YlGnBu", vmin=0, vmax=25)
ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels([f"+{c}月" for c in piv.columns])
ax.set_yticks(range(len(piv.index))); ax.set_yticklabels([f"{c} (n={cohort_size[c]:,})" for c in piv.index])
for i in range(len(piv.index)):
    for j in range(len(piv.columns)):
        v = piv.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8)
ax.set_title("月度 Cohort 留存率（%）：平台以一次性购买为主，复购极低")
plt.colorbar(im, ax=ax, shrink=0.8)
plt.tight_layout(); plt.savefig(os.path.join(CH, "07_留存热力图.png"), dpi=150); plt.close()

# ---------- 8. 品类 GMV ----------
cat = q("""
SELECT COALESCE(t.product_category_name_english, p.product_category_name) AS cat,
       COUNT(DISTINCT i.order_id) AS orders,
       ROUND(SUM(i.price+i.freight_value),2) AS gmv
FROM olist_order_items i
LEFT JOIN olist_products p ON i.product_id=p.product_id
LEFT JOIN olist_product_category_translation t ON p.product_category_name=t.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY gmv DESC LIMIT 15
""")
cat = cat.rename(columns={"cat": "类目", "orders": "订单数", "gmv": "GMV_BRL"})
cat.to_csv(os.path.join(EX, "category_gmv.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(cat["类目"][::-1], cat["GMV_BRL"][::-1], color="#55A868")
ax.set_xlabel("GMV (BRL)"); ax.set_title("类目 GMV Top 15")
for b, v in zip(ax.patches, cat["GMV_BRL"][::-1]):
    ax.text(b.get_width() + 20000, b.get_y() + b.get_height()/2, f"{v/10000:.1f}万", va="center", fontsize=9)
plt.tight_layout(); plt.savefig(os.path.join(CH, "08_品类GMV.png"), dpi=150); plt.close()

# ---------- 9. 州 GMV ----------
st = q("""
SELECT cu.customer_state AS state, COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(p.payment_value),2) AS gmv
FROM olist_orders o JOIN olist_customers cu ON o.customer_id=cu.customer_id
JOIN olist_order_payments p ON o.order_id=p.order_id
GROUP BY cu.customer_state ORDER BY gmv DESC LIMIT 10
""")
st.to_csv(os.path.join(EX, "state_gmv.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(st["state"], st["gmv"], color="#4C72B0")
for i, (x, y) in enumerate(zip(st["state"], st["gmv"])):
    ax.text(i, y + 50000, f"{y/10000:.0f}万", ha="center", fontsize=9)
ax.set_ylabel("GMV (BRL)"); ax.set_title("州 GMV Top 10：SP 占 37.5%")
plt.tight_layout(); plt.savefig(os.path.join(CH, "09_州GMV.png"), dpi=150); plt.close()

# ---------- 10. 评分分布 ----------
rev = q("""
SELECT review_score AS score, COUNT(*) AS n FROM olist_order_reviews GROUP BY review_score ORDER BY review_score
""")
rev.to_csv(os.path.join(EX, "reviews.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(rev["score"].astype(str), rev["n"], color=["#C44E52", "#DD8452", "#DD8452", "#55A868", "#4C72B0"])
for i, (x, y) in enumerate(zip(rev["score"].astype(str), rev["n"])):
    ax.text(i, y + 800, f"{y:,} ({y/rev['n'].sum()*100:.1f}%)", ha="center", fontsize=9)
ax.set_xlabel("评分"); ax.set_ylabel("评价数"); ax.set_title("评价评分分布：平均 4.09，两极分化(J 型)")
plt.tight_layout(); plt.savefig(os.path.join(CH, "10_评分分布.png"), dpi=150); plt.close()

# ---------- 11. 配送时效 ----------
dlv = q("""
SELECT DATEDIFF(order_delivered_customer_date, order_purchase_timestamp) AS days,
       DATEDIFF(order_estimated_delivery_date, order_purchase_timestamp) AS est
FROM olist_orders
WHERE order_status='delivered' AND order_delivered_customer_date IS NOT NULL
  AND order_purchase_timestamp IS NOT NULL AND order_estimated_delivery_date IS NOT NULL
""")
dlv.to_csv(os.path.join(EX, "delivery.csv"), index=False, encoding="utf-8-sig")
fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(dlv["days"], bins=40, color="#8172B3", alpha=0.85, label="实际送达天数")
ax.hist(dlv["est"], bins=40, color="#4C72B0", alpha=0.45, label="承诺天数")
ax.set_xlabel("天数"); ax.set_ylabel("订单数"); ax.set_xlim(0, 80)
late = (dlv["days"] > dlv["est"]).mean() * 100
ax.set_title(f"配送时效：实际平均 {dlv['days'].mean():.1f} 天 vs 承诺 {dlv['est'].mean():.1f} 天，晚到率 {late:.1f}%")
ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(CH, "11_配送时效.png"), dpi=150); plt.close()

conn.close()
print("完成: 导出", len(os.listdir(EX)), "个 CSV, 图表", len(os.listdir(CH)), "张")
