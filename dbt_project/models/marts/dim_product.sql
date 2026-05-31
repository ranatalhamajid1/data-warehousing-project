-- models/marts/dim_product.sql
-- Product dimension with competitor pricing enrichment

{{ config(
    materialized = 'table',
    schema = 'marts',
    tags = ['marts', 'dimension']
) }}

WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

competitor_agg AS (
    SELECT
        product_name,
        category,
        AVG(competitor_price_usd)        AS avg_competitor_price,
        MIN(competitor_price_usd)        AS min_competitor_price,
        MAX(competitor_price_usd)        AS max_competitor_price,
        COUNT(DISTINCT competitor_name)  AS num_competitors,
        LISTAGG(DISTINCT competitor_name, ', ') WITHIN GROUP (ORDER BY competitor_name) AS competitors
    FROM {{ ref('stg_competitor_prices') }}
    GROUP BY product_name, category
),

sales_agg AS (
    SELECT
        oi.product_id,
        COUNT(DISTINCT oi.order_id)            AS times_ordered,
        SUM(oi.quantity)                       AS units_sold,
        SUM(oi.line_revenue)                   AS total_revenue
    FROM {{ ref('stg_order_items') }} oi
    GROUP BY oi.product_id
),

final AS (
    SELECT
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['p.product_id']) }}  AS product_key,

        -- Natural key
        p.product_id,

        -- Attributes
        p.product_name,
        p.category,
        p.retail_price,
        p.base_cost,
        p.gross_margin_pct,
        p.price_tier,

        -- Competitor pricing
        c.avg_competitor_price,
        c.min_competitor_price,
        c.max_competitor_price,
        c.num_competitors,
        c.competitors,

        -- Competitor delta
        ROUND(p.retail_price - COALESCE(c.avg_competitor_price, p.retail_price), 2) AS price_vs_avg_competitor,
        CASE
            WHEN c.avg_competitor_price IS NULL              THEN 'No Competitor Data'
            WHEN p.retail_price > c.avg_competitor_price * 1.05 THEN 'Overpriced'
            WHEN p.retail_price < c.avg_competitor_price * 0.95 THEN 'Underpriced'
            ELSE 'Competitive'
        END AS competitive_position,

        -- Sales performance
        COALESCE(s.times_ordered, 0)    AS times_ordered,
        COALESCE(s.units_sold, 0)       AS units_sold,
        COALESCE(s.total_revenue, 0)    AS total_revenue,

        CURRENT_TIMESTAMP()             AS dw_created_at,
        CURRENT_TIMESTAMP()             AS dw_updated_at

    FROM products p
    LEFT JOIN competitor_agg c ON LOWER(TRIM(p.product_name)) = LOWER(TRIM(c.product_name))
    LEFT JOIN sales_agg      s ON p.product_id = s.product_id
)

SELECT * FROM final
