-- =============================================================
-- 04 时间规律：月度 / 星期 / 小时
-- =============================================================

-- 4.1 月度订单数与 GMV
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS 月份,
    COUNT(DISTINCT o.order_id)                        AS 订单数,
    ROUND(SUM(p.payment_value), 2)                    AS GMV_BRL
FROM olist_orders o
LEFT JOIN olist_order_payments p ON o.order_id = p.order_id
GROUP BY 月份
ORDER BY 月份;

-- 4.2 星期分布（1=周日 ... 7=周六）
SELECT
    DAYOFWEEK(o.order_purchase_timestamp) AS 星期,
    COUNT(*)                              AS 订单数
FROM olist_orders o
GROUP BY 星期
ORDER BY 星期;

-- 4.3 小时分布
SELECT
    HOUR(o.order_purchase_timestamp) AS 小时,
    COUNT(*)                         AS 订单数
FROM olist_orders o
GROUP BY 小时
ORDER BY 小时;
