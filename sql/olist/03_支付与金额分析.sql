-- =============================================================
-- 03 支付方式与金额分析（GMV / 客单价 / 集中度）
-- =============================================================

-- 3.1 GMV 与客单价（按订单聚合支付额）
SELECT
    COUNT(*)                     AS 订单数,
    ROUND(SUM(payment_value), 2) AS 总GMV_BRL,
    ROUND(AVG(payment_value), 2) AS 客单价_BRL,
    ROUND(MAX(payment_value), 2) AS 最大单_BRL,
    ROUND(MIN(payment_value), 2) AS 最小单_BRL
FROM (
    SELECT order_id, SUM(payment_value) AS payment_value
    FROM olist_order_payments
    GROUP BY order_id
) t;

-- 3.2 支付方式结构
SELECT
    payment_type AS 支付方式,
    COUNT(*)     AS 笔数,
    ROUND(SUM(payment_value), 2) AS 金额_BRL,
    ROUND(SUM(payment_value) * 100.0 / SUM(SUM(payment_value)) OVER (), 2) AS 金额占比_pct
FROM olist_order_payments
GROUP BY payment_type
ORDER BY 金额占比_pct DESC;

-- 3.3 分期数分布（信用卡分期）
SELECT
    payment_installments AS 分期数,
    COUNT(*)             AS 笔数
FROM olist_order_payments
GROUP BY payment_installments
ORDER BY 笔数 DESC
LIMIT 10;

-- 3.4 订单金额集中度：Top 1% / 10% / 20% 订单占 GMV 比例
WITH order_value AS (
    SELECT order_id, SUM(payment_value) AS v
    FROM olist_order_payments
    GROUP BY order_id
),
ranked AS (
    SELECT v,
           ROW_NUMBER() OVER (ORDER BY v DESC) AS rn,
           COUNT(*) OVER ()                    AS total
    FROM order_value
)
SELECT
    ROUND(100.0 * SUM(CASE WHEN rn <= total * 0.01 THEN v ELSE 0 END) / SUM(v), 2) AS Top1订单GMV占比_pct,
    ROUND(100.0 * SUM(CASE WHEN rn <= total * 0.10 THEN v ELSE 0 END) / SUM(v), 2) AS Top10订单GMV占比_pct,
    ROUND(100.0 * SUM(CASE WHEN rn <= total * 0.20 THEN v ELSE 0 END) / SUM(v), 2) AS Top20订单GMV占比_pct
FROM ranked;
