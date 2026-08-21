-- =============================================================
-- 02 订单状态漏斗（真实运营漏斗）
-- Olist 无浏览/加购日志，用订单生命周期时间戳构建漏斗：
--   下单 → 付款批准 → 发货 → 送达 / 取消
-- =============================================================

-- 2.1 生命周期漏斗（按时间戳口径）
SELECT
    COUNT(*)                                              AS 下单订单数,
    SUM(order_approved_at IS NOT NULL)                     AS 付款批准,
    SUM(order_delivered_carrier_date IS NOT NULL)          AS 已发货,
    SUM(order_delivered_customer_date IS NOT NULL)         AS 已送达,
    SUM(order_status = 'canceled')                         AS 已取消
FROM olist_orders;

-- 2.2 终态分布
SELECT
    order_status            AS 订单状态,
    COUNT(*)                AS 订单数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS 占比_pct
FROM olist_orders
GROUP BY order_status
ORDER BY 订单数 DESC;

-- 2.3 各阶段转化率与取消率
SELECT
    ROUND(SUM(order_approved_at IS NOT NULL) * 100.0 / COUNT(*), 2)        AS 下单到付款批准_pct,
    ROUND(SUM(order_delivered_carrier_date IS NOT NULL) * 100.0 / COUNT(*), 2) AS 付款到发货_pct,
    ROUND(SUM(order_delivered_customer_date IS NOT NULL) * 100.0 / COUNT(*), 2) AS 发货到送达_pct,
    ROUND(SUM(order_status = 'canceled') * 100.0 / COUNT(*), 2)            AS 取消率_pct
FROM olist_orders;
