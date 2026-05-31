-- models/analytics/competitor_pricing_index.sql
-- Competitive pricing intelligence dashboard model

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics', 'competitor']
) }}

WITH fct AS (
    SELECT
        category,
        product_id,
        AVG(unit_price)              AS avg_our_price,
        AVG(competitor_price_delta)  AS avg_price_delta,
        SUM(revenue)                 AS total_revenue,
        SUM(gross_margin)            AS total_margin,
        COUNT(DISTINCT order_id)     AS order_count
    FROM {{ ref('fct_sales') }}
    WHERE competitor_price_delta IS NOT NULL
    GROUP BY category, product_id
),

competitor AS (
    SELECT * FROM {{ ref('stg_competitor_prices') }}
),

product_competitor AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        p.retail_price,
        p.avg_competitor_price,
        p.min_competitor_price,
        p.max_competitor_price,
        p.num_competitors,
        p.competitive_position,
        p.price_vs_avg_competitor
    FROM {{ ref('dim_product') }} p
    WHERE p.avg_competitor_price IS NOT NULL
),

category_index AS (
    SELECT
        pc.category,
        COUNT(pc.product_id)                           AS products_tracked,
        AVG(pc.retail_price)                           AS avg_our_retail_price,
        AVG(pc.avg_competitor_price)                   AS avg_competitor_price,
        AVG(pc.retail_price - pc.avg_competitor_price) AS avg_price_delta,
        SUM(CASE WHEN pc.competitive_position = 'Overpriced'   THEN 1 ELSE 0 END) AS overpriced_count,
        SUM(CASE WHEN pc.competitive_position = 'Underpriced'  THEN 1 ELSE 0 END) AS underpriced_count,
        SUM(CASE WHEN pc.competitive_position = 'Competitive'  THEN 1 ELSE 0 END) AS competitive_count,

        -- Price index: 100 = parity, >100 = we're more expensive
        ROUND(AVG(pc.retail_price) / NULLIF(AVG(pc.avg_competitor_price), 0) * 100, 2) AS price_index

    FROM product_competitor pc
    GROUP BY pc.category
),

final AS (
    SELECT
        ci.*,
        f.total_revenue,
        f.total_margin,
        f.order_count,

        -- Risk score: overpriced products with high revenue = high risk
        ROUND(ci.overpriced_count::FLOAT / NULLIF(ci.products_tracked, 0) * 100, 1) AS pct_overpriced,
        CASE
            WHEN ci.price_index > 110 THEN 'High Risk — Significantly Overpriced'
            WHEN ci.price_index > 105 THEN 'Medium Risk — Slightly Overpriced'
            WHEN ci.price_index < 90  THEN 'Opportunity — Underpriced'
            ELSE 'Healthy — Competitive Pricing'
        END AS pricing_health

    FROM category_index ci
    LEFT JOIN (
        SELECT category, SUM(total_revenue) AS total_revenue,
               SUM(total_margin) AS total_margin, SUM(order_count) AS order_count
        FROM fct
        GROUP BY category
    ) f ON ci.category = f.category
)

SELECT * FROM final
ORDER BY price_index DESC
