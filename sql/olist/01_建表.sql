-- =============================================================
-- Olist 巴西电商真实数据集 - 建表 (ecommerce 库, olist_ 前缀)
-- 数据来源: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
-- 时间范围: 2016-09 ~ 2018-10
-- =============================================================

DROP TABLE IF EXISTS olist_order_reviews;
DROP TABLE IF EXISTS olist_order_payments;
DROP TABLE IF EXISTS olist_order_items;
DROP TABLE IF EXISTS olist_orders;
DROP TABLE IF EXISTS olist_customers;
DROP TABLE IF EXISTS olist_geolocation;
DROP TABLE IF EXISTS olist_products;
DROP TABLE IF EXISTS olist_sellers;
DROP TABLE IF EXISTS olist_product_category_translation;

CREATE TABLE olist_customers (
    customer_id            VARCHAR(32) NOT NULL,
    customer_unique_id     VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INT NULL,
    customer_city          VARCHAR(64) NULL,
    customer_state         CHAR(2) NULL,
    PRIMARY KEY (customer_id),
    KEY idx_customer_unique (customer_unique_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_geolocation (
    geolocation_zip_code_prefix INT NULL,
    geolocation_lat        DECIMAL(10,7) NULL,
    geolocation_lng        DECIMAL(10,7) NULL,
    geolocation_city       VARCHAR(64) NULL,
    geolocation_state      CHAR(2) NULL,
    KEY idx_geo_zip (geolocation_zip_code_prefix)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_orders (
    order_id                   VARCHAR(32) NOT NULL,
    customer_id                VARCHAR(32) NOT NULL,
    order_status               VARCHAR(16) NULL,
    order_purchase_timestamp   DATETIME NULL,
    order_approved_at          DATETIME NULL,
    order_delivered_carrier_date DATETIME NULL,
    order_delivered_customer_date DATETIME NULL,
    order_estimated_delivery_date DATETIME NULL,
    PRIMARY KEY (order_id),
    KEY idx_orders_customer (customer_id),
    KEY idx_orders_time (order_purchase_timestamp),
    KEY idx_orders_status (order_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_order_items (
    order_id             VARCHAR(32) NOT NULL,
    order_item_id        INT NOT NULL,
    product_id           VARCHAR(32) NOT NULL,
    seller_id            VARCHAR(32) NOT NULL,
    shipping_limit_date  DATETIME NULL,
    price                DECIMAL(10,2) NULL,
    freight_value        DECIMAL(10,2) NULL,
    PRIMARY KEY (order_id, order_item_id),
    KEY idx_items_product (product_id),
    KEY idx_items_seller (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_order_payments (
    order_id            VARCHAR(32) NOT NULL,
    payment_sequential  INT NOT NULL,
    payment_type        VARCHAR(16) NULL,
    payment_installments INT NULL,
    payment_value       DECIMAL(10,2) NULL,
    PRIMARY KEY (order_id, payment_sequential),
    KEY idx_pay_type (payment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_order_reviews (
    review_id              VARCHAR(32) NOT NULL,
    order_id               VARCHAR(32) NOT NULL,
    review_score           TINYINT NULL,
    review_comment_title   TEXT NULL,
    review_comment_message TEXT NULL,
    review_creation_date   DATETIME NULL,
    review_answer_timestamp DATETIME NULL,
    KEY idx_review_order (order_id),
    KEY idx_review_id (review_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_products (
    product_id               VARCHAR(32) NOT NULL,
    product_category_name    VARCHAR(64) NULL,
    product_name_length      INT NULL,
    product_description_length INT NULL,
    product_photos_qty       INT NULL,
    product_weight_g         INT NULL,
    product_length_cm        INT NULL,
    product_height_cm        INT NULL,
    product_width_cm         INT NULL,
    PRIMARY KEY (product_id),
    KEY idx_product_category (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_sellers (
    seller_id            VARCHAR(32) NOT NULL,
    seller_zip_code_prefix INT NULL,
    seller_city          VARCHAR(64) NULL,
    seller_state         CHAR(2) NULL,
    PRIMARY KEY (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE olist_product_category_translation (
    product_category_name        VARCHAR(64) NOT NULL,
    product_category_name_english VARCHAR(64) NULL,
    PRIMARY KEY (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
