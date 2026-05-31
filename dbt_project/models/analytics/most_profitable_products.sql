-- models/analytics/most_profitable_products.sql
-- Most profitable products by margin and revenue

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics', 'products']
) }}

WITH fct AS (
    SELECT * FROM {{ ref('fct_sales') }}
),

dim_product AS (
    SELECT * FROM {{ ref('dim_product') }}
),

product_metrics AS (
    SELECT
        f.product_id,
        f.category,
        COUNT(DISTINCT f.order_id)    AS times_ordered,
        COUNT(DISTINCT f.customer_id) AS unique_buyers,
        SUM(f.quantity)               AS total_units_sold,
        SUM(f.revenue)                AS total_revenue,
        SUM(f.gross_margin)           AS total_gross_margin,
        SUM(f.cogs)                   AS total_cogs,
        SUM(f.discount_amount)        AS total_discounts_given,
        AVG(f.gross_margin_pct)       AS avg_margin_pct,
        AVG(f.unit_price)             AS avg_selling_price,
        MIN(f.unit_price)             AS min_selling_price,
        MAX(f.unit_price)             AS max_selling_price,
        MIN(f.order_date)             AS first_sale_date,
        MAX(f.order_date)             AS last_sale_date,
        AVG(f.competitor_price_delta) AS avg_competitor_delta

    FROM fct f
    GROUP BY f.product_id, f.category
),

ranked AS (
    SELECT
        pm.*,
        dp.product_name,
        dp.retail_price,
        dp.base_cost,
        dp.gross_margin_pct     AS list_margin_pct,
        dp.price_tier,
        dp.competitive_position,
        dp.avg_competitor_price,
        dp.num_competitors,

        -- Rankings
        RANK() OVER (ORDER BY pm.total_gross_margin DESC) AS margin_rank,
        RANK() OVER (ORDER BY pm.total_revenue DESC)      AS revenue_rank,
        RANK() OVER (ORDER BY pm.total_units_sold DESC)   AS volume_rank,
        RANK() OVER (ORDER BY pm.avg_margin_pct DESC)     AS margin_pct_rank,

        -- Category rank
        RANK() OVER (PARTITION BY pm.category ORDER BY pm.total_gross_margin DESC) AS category_margin_rank,
        RANK() OVER (PARTITION BY pm.category ORDER BY pm.total_revenue DESC)      AS category_revenue_rank,

        -- Profit efficiency score (margin per unit × volume rank percentile)
        ROUND(pm.total_gross_margin / NULLIF(pm.total_units_sold, 0), 2) AS margin_per_unit,

        IFF(pm.total_gross_margin > 0, TRUE, FALSE) AS is_profitable

    FROM product_metrics pm
    JOIN dim_product dp ON pm.product_id = dp.product_id
),

final AS (
    SELECT
        margin_rank,
        revenue_rank,
        product_id,
        product_name,
        category,
        price_tier,
        retail_price,
        base_cost,
        avg_selling_price,
        competitive_position,
        avg_competitor_price,
        avg_competitor_delta,
        num_competitors,
        total_units_sold,
        times_ordered,
        unique_buyers,
        ROUND(total_revenue, 2)          AS total_revenue,
        ROUND(total_gross_margin, 2)     AS total_gross_margin,
        ROUND(total_cogs, 2)             AS total_cogs,
        ROUND(total_discounts_given, 2)  AS total_discounts_given,
        ROUND(avg_margin_pct, 2)         AS avg_realized_margin_pct,
        ROUND(list_margin_pct, 2)        AS list_margin_pct,
        ROUND(margin_per_unit, 2)        AS margin_per_unit,
        first_sale_date,
        last_sale_date,
        category_margin_rank,
        category_revenue_rank,
        margin_pct_rank,
        volume_rank,
        is_profitable,

        -- Performance label
        CASE
            WHEN margin_rank <= 10  AND revenue_rank <= 10  THEN 'Star Product'
            WHEN margin_rank <= 50  AND revenue_rank <= 50  THEN 'Strong Performer'
            WHEN margin_rank > 400  AND revenue_rank > 400  THEN 'Low Performer'
            WHEN avg_margin_pct > 50                        THEN 'High Margin Niche'
            ELSE 'Average'
        END AS performance_label

    FROM ranked
)

SELECT * FROM final
ORDER BY margin_rank
