-- models/analytics/top_categories.sql
-- Category performance analytics

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics']
) }}

WITH fct AS (
    SELECT * FROM {{ ref('fct_sales') }}
),

category_monthly AS (
    SELECT
        f.category,
        DATE_TRUNC('month', f.order_date)   AS month_start,
        YEAR(f.order_date)                  AS year_number,
        MONTH(f.order_date)                 AS month_number,

        COUNT(DISTINCT f.order_id)          AS orders,
        COUNT(DISTINCT f.customer_id)       AS unique_customers,
        SUM(f.quantity)                     AS units_sold,
        SUM(f.revenue)                      AS total_revenue,
        SUM(f.gross_margin)                 AS total_margin,
        AVG(f.gross_margin_pct)             AS avg_margin_pct,
        AVG(f.unit_price)                   AS avg_selling_price,
        SUM(f.discount_amount)              AS total_discounts

    FROM fct f
    GROUP BY
        f.category,
        DATE_TRUNC('month', f.order_date),
        YEAR(f.order_date),
        MONTH(f.order_date)
),

overall_category AS (
    SELECT
        category,
        SUM(total_revenue)         AS yearly_revenue,
        SUM(total_margin)          AS yearly_margin,
        SUM(units_sold)            AS yearly_units,
        SUM(orders)                AS yearly_orders,
        AVG(avg_margin_pct)        AS overall_margin_pct,
        RANK() OVER (ORDER BY SUM(total_revenue) DESC) AS revenue_rank
    FROM category_monthly
    GROUP BY category
),

final AS (
    SELECT
        cm.*,
        oc.yearly_revenue,
        oc.yearly_margin,
        oc.yearly_units,
        oc.yearly_orders,
        oc.overall_margin_pct,
        oc.revenue_rank,

        -- Market share within year
        ROUND(cm.total_revenue / oc.yearly_revenue * 100, 2) AS monthly_revenue_share_pct,

        -- Month-over-month growth within category
        LAG(cm.total_revenue) OVER (PARTITION BY cm.category ORDER BY cm.month_start) AS prev_month_revenue,
        ROUND(
            (cm.total_revenue - LAG(cm.total_revenue) OVER (PARTITION BY cm.category ORDER BY cm.month_start))
            / NULLIF(LAG(cm.total_revenue) OVER (PARTITION BY cm.category ORDER BY cm.month_start), 0) * 100, 2
        ) AS mom_growth_pct

    FROM category_monthly cm
    JOIN overall_category oc ON cm.category = oc.category
)

SELECT * FROM final
ORDER BY yearly_revenue DESC, month_start
