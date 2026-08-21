-- =============================================================
-- 06 复购与留存（Cohort 月度留存）
-- =============================================================

-- 6.1 复购率总览：单次购买 vs 复购
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        COUNT(DISTINCT o.order_id) AS F_单
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
)
SELECT
    SUM(F_单 = 1) AS 单次购买客户,
    SUM(F_单 >= 2) AS 复购客户,
    ROUND(SUM(F_单 >= 2) * 100.0 / COUNT(*), 2) AS 复购率_pct
FROM cus;

-- 6.2 月度 Cohort 留存明细（首购月 x 购买月偏移）
-- month_offset=0 为该 cohort 全部客户数（即 cohort 规模）
WITH base AS (
    SELECT
        c.customer_unique_id AS 客户,
        DATE_FORMAT(MIN(o.order_purchase_timestamp), '%Y-%m') AS cohort_month,
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')      AS buy_month
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id, DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT
    cohort_month AS 首购月份,
    TIMESTAMPDIFF(MONTH, CONCAT(cohort_month, '-01'), CONCAT(buy_month, '-01')) AS 第几月,
    COUNT(DISTINCT 客户) AS 活跃客户数
FROM base
GROUP BY cohort_month, 第几月
ORDER BY cohort_month, 第几月;
