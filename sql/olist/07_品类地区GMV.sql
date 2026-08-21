-- =============================================================
-- 07 品类与地区 GMV 分析
-- =============================================================

-- 7.1 类目 GMV Top 15（商品金额 + 运费）
SELECT
    COALESCE(t.product_category_name_english, p.product_category_name) AS 类目,
    COUNT(DISTINCT i.order_id) AS 订单数,
    ROUND(SUM(i.price + i.freight_value), 2) AS GMV_BRL,
    ROUND(SUM(i.price + i.freight_value) * 100.0
          / SUM(SUM(i.price + i.freight_value)) OVER (), 2) AS GMV占比_pct
FROM olist_order_items i
LEFT JOIN olist_products p ON i.product_id = p.product_id
LEFT JOIN olist_product_category_translation t
       ON p.product_category_name = t.product_category_name
GROUP BY COALESCE(t.product_category_name_english, p.product_category_name)
ORDER BY GMV_BRL DESC
LIMIT 15;

-- 7.2 州 GMV Top 10
SELECT
    cu.customer_state AS 州,
    COUNT(DISTINCT o.order_id) AS 订单数,
    ROUND(SUM(p.payment_value), 2) AS GMV_BRL,
    ROUND(SUM(p.payment_value) * 100.0 / SUM(SUM(p.payment_value)) OVER (), 2) AS GMV占比_pct
FROM olist_orders o
JOIN olist_customers cu ON o.customer_id = cu.customer_id
JOIN olist_order_payments p ON o.order_id = p.order_id
GROUP BY cu.customer_state
ORDER BY GMV_BRL DESC
LIMIT 10;

-- 7.3 城市 GMV Top 10
SELECT
    cu.customer_city  AS 城市,
    cu.customer_state AS 州,
    COUNT(DISTINCT o.order_id) AS 订单数,
    ROUND(SUM(p.payment_value), 2) AS GMV_BRL
FROM olist_orders o
JOIN olist_customers cu ON o.customer_id = cu.customer_id
JOIN olist_order_payments p ON o.order_id = p.order_id
GROUP BY cu.customer_city, cu.customer_state
ORDER BY GMV_BRL DESC
LIMIT 10;
