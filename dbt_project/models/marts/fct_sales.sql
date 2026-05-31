-- models/marts/fct_sales.sql
-- Central fact table: one row per order line item
-- Metrics: quantity, revenue, margin, competitor_price_delta

{{ config(
    materialized = 'table',
    schema = 'marts',
    tags = ['marts', 'fact'],
    cluster_by = ['order_date', 'category']
) }}

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

dim_customer AS (
    SELECT customer_key, customer_id FROM {{ ref('dim_customer') }}
),

dim_product AS (
    SELECT
        product_key,
        product_id,
        retail_price,
        base_cost,
        gross_margin_pct,
        category,
        competitive_position,
        avg_competitor_price
    FROM {{ ref('dim_product') }}
),

dim_date AS (
    SELECT date_key, date_actual FROM {{ ref('dim_date') }}
),

joined AS (
    SELECT
        -- Surrogate key for the fact row
        {{ dbt_utils.generate_surrogate_key(['oi.order_item_id']) }} AS sales_key,

        -- Foreign keys to dimensions
        dc.customer_key,
        dp.product_key,
        dd.date_key,

        -- Degenerate dimensions (natural keys)
        oi.order_item_id,
        oi.order_id,
        o.customer_id,
        oi.product_id,
        o.order_date,

        -- Category (denormalized for filtering performance)
        dp.category,

        -- ── Additive Measures ─────────────────────────────────────────────────

        -- Quantity
        oi.quantity,

        -- Revenue = qty × unit_price sold
        oi.unit_price                                                   AS unit_price,
        oi.line_revenue                                                  AS revenue,

        -- Cost of goods sold
        ROUND(dp.base_cost * oi.quantity, 2)                            AS cogs,

        -- Gross margin (revenue - cogs)
        ROUND(oi.line_revenue - (dp.base_cost * oi.quantity), 2)        AS gross_margin,

        -- Gross margin % at line level
        CASE
            WHEN oi.line_revenue > 0
            THEN ROUND((oi.line_revenue - dp.base_cost * oi.quantity) / oi.line_revenue * 100, 2)
            ELSE 0
        END AS gross_margin_pct,

        -- Discount given vs. retail price
        ROUND((dp.retail_price - oi.unit_price) * oi.quantity, 2)      AS discount_amount,
        CASE
            WHEN dp.retail_price > 0
            THEN ROUND((dp.retail_price - oi.unit_price) / dp.retail_price * 100, 2)
            ELSE 0
        END AS discount_pct,

        -- Competitor price delta
        -- Positive = we are selling ABOVE competitor average (potential lost sales)
        -- Negative = we are selling BELOW competitor average (competitive advantage)
        CASE
            WHEN dp.avg_competitor_price IS NOT NULL AND dp.avg_competitor_price > 0
            THEN ROUND(oi.unit_price - dp.avg_competitor_price, 2)
            ELSE NULL
        END AS competitor_price_delta,

        CASE
            WHEN dp.avg_competitor_price IS NOT NULL AND dp.avg_competitor_price > 0
            THEN ROUND((oi.unit_price - dp.avg_competitor_price) / dp.avg_competitor_price * 100, 2)
            ELSE NULL
        END AS competitor_price_delta_pct,

        -- Competitive position flag for easy filtering
        dp.competitive_position,

        CURRENT_TIMESTAMP() AS dw_created_at

    FROM order_items oi
    JOIN orders         o  ON oi.order_id   = o.order_id
    JOIN dim_customer  dc  ON o.customer_id = dc.customer_id
    JOIN dim_product   dp  ON oi.product_id = dp.product_id
    JOIN dim_date      dd  ON o.order_date  = dd.date_actual
)

SELECT * FROM joined
