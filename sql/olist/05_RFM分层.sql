-- =============================================================
-- 05 客户价值分层：R(最近购买) + M(消费金额)；F(频次)单独看
-- 背景：Olist 96.9% 客户只买过 1 单，F 无区分度，故采用 R+M 分层
-- =============================================================

-- 5.0 R/M/F 三指标描述统计
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        DATEDIFF((SELECT MAX(order_purchase_timestamp) FROM olist_orders),
                 MAX(o.order_purchase_timestamp)) AS R_天,
        COUNT(DISTINCT o.order_id) AS F_单,
        COALESCE(SUM(p.payment_value), 0) AS M_BRL
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    LEFT JOIN olist_order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*)          AS 客户数,
    ROUND(AVG(R_天), 1) AS R平均_天,
    ROUND(AVG(F_单), 3) AS F平均_单,
    ROUND(MAX(F_单))    AS F最大,
    ROUND(AVG(M_BRL), 2) AS M平均_BRL
FROM cus;

-- 5.1 F 分布（验证频次无区分度）
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        COUNT(DISTINCT o.order_id) AS F_单
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
)
SELECT
    F_单 AS 购买次数,
    COUNT(*) AS 客户数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS 占比_pct
FROM cus
GROUP BY F_单
ORDER BY F_单;

-- 5.2 M 分层（三分位：高 / 中 / 低）
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        COALESCE(SUM(p.payment_value), 0) AS M_BRL
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    LEFT JOIN olist_order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
),
tiered AS (
    SELECT 客户, M_BRL,
           NTILE(3) OVER (ORDER BY M_BRL DESC) AS m_tier
    FROM cus
)
SELECT
    CASE m_tier WHEN 1 THEN 'M高' WHEN 2 THEN 'M中' ELSE 'M低' END AS 消费分层,
    COUNT(*)  AS 客户数,
    ROUND(SUM(M_BRL), 2) AS GMV_BRL,
    ROUND(SUM(M_BRL) * 100.0 / SUM(SUM(M_BRL)) OVER (), 2) AS GMV占比_pct,
    ROUND(AVG(M_BRL), 2) AS 人均_BRL
FROM tiered
GROUP BY m_tier
ORDER BY m_tier;

-- 5.3 R 分层（三分位：近 / 中 / 远）
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        DATEDIFF((SELECT MAX(order_purchase_timestamp) FROM olist_orders),
                 MAX(o.order_purchase_timestamp)) AS R_天
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_unique_id
),
tiered AS (
    SELECT 客户, R_天,
           NTILE(3) OVER (ORDER BY R_天 ASC) AS r_tier
    FROM cus
)
SELECT
    CASE r_tier WHEN 1 THEN 'R近' WHEN 2 THEN 'R中' ELSE 'R远' END AS 最近购买,
    COUNT(*)  AS 客户数,
    ROUND(AVG(R_天), 1) AS 平均R_天,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS 占比_pct
FROM tiered
GROUP BY r_tier
ORDER BY r_tier;

-- 5.4 R × M 矩阵：客户数与 GMV 贡献
WITH cus AS (
    SELECT
        c.customer_unique_id AS 客户,
        DATEDIFF((SELECT MAX(order_purchase_timestamp) FROM olist_orders),
                 MAX(o.order_purchase_timestamp)) AS R_天,
        COALESCE(SUM(p.payment_value), 0) AS M_BRL
    FROM olist_orders o
    JOIN olist_customers c ON o.customer_id = c.customer_id
    LEFT JOIN olist_order_payments p ON o.order_id = p.order_id
    GROUP BY c.customer_unique_id
),
tiered AS (
    SELECT 客户, R_天, M_BRL,
           NTILE(3) OVER (ORDER BY M_BRL DESC) AS m_tier,
           NTILE(3) OVER (ORDER BY R_天 ASC)  AS r_tier
    FROM cus
)
SELECT
    CASE r_tier WHEN 1 THEN 'R近' WHEN 2 THEN 'R中' ELSE 'R远' END AS 最近购买,
    CASE m_tier WHEN 1 THEN 'M高' WHEN 2 THEN 'M中' ELSE 'M低' END AS 消费金额,
    COUNT(*)  AS 客户数,
    ROUND(SUM(M_BRL), 2) AS GMV_BRL,
    ROUND(SUM(M_BRL) * 100.0 / SUM(SUM(M_BRL)) OVER (), 2) AS GMV占比_pct,
    ROUND(AVG(M_BRL), 2) AS 人均_BRL
FROM tiered
GROUP BY r_tier, m_tier
ORDER BY r_tier, m_tier;
