-- =============================================================
-- 08 评价与物流时效分析
-- =============================================================

-- 8.1 评分分布
SELECT
    review_score AS 评分,
    COUNT(*) AS 条数,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS 占比_pct
FROM olist_order_reviews
GROUP BY review_score
ORDER BY review_score;

-- 8.2 总体平均评分
SELECT
    ROUND(AVG(review_score), 2) AS 平均评分,
    COUNT(*) AS 评价数
FROM olist_order_reviews;

-- 8.3 物流时效（已送达订单）
SELECT
    COUNT(*) AS 送达订单,
    ROUND(AVG(DATEDIFF(order_delivered_customer_date, order_purchase_timestamp)), 1) AS 平均送达天数,
    ROUND(AVG(DATEDIFF(order_estimated_delivery_date, order_purchase_timestamp)), 1) AS 平均承诺天数,
    ROUND(SUM(order_delivered_customer_date > order_estimated_delivery_date) * 100.0 / COUNT(*), 2) AS 晚到率_pct,
    ROUND(AVG(DATEDIFF(order_estimated_delivery_date, order_delivered_customer_date)), 1) AS 平均提前天数
FROM olist_orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL;

-- 8.4 类目平均评分（评价数 >= 500 的类目，按评分升序取 10）
WITH order_cat AS (
    SELECT
        i.order_id,
        COALESCE(t.product_category_name_english, p.product_category_name) AS cat,
        ROW_NUMBER() OVER (PARTITION BY i.order_id ORDER BY (i.price + i.freight_value) DESC) AS rn
    FROM olist_order_items i
    JOIN olist_products p ON i.product_id = p.product_id
    LEFT JOIN olist_product_category_translation t
           ON p.product_category_name = t.product_category_name
)
SELECT
    oc.cat AS 类目,
    COUNT(*) AS 评价数,
    ROUND(AVG(r.review_score), 2) AS 平均评分
FROM olist_order_reviews r
JOIN order_cat oc ON r.order_id = oc.order_id AND oc.rn = 1
GROUP BY oc.cat
HAVING COUNT(*) >= 500
ORDER BY 平均评分 ASC
LIMIT 10;
