-- models/analytics/daily_revenue.sql
-- Pre-aggregated daily revenue trends for dashboard

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics']
) }}

WITH fct AS (
    SELECT * FROM {{ ref('fct_sales') }}
),

dim_date AS (
    SELECT * FROM {{ ref('dim_date') }}
),

daily AS (
    SELECT
        f.order_date,
        d.year_number,
        d.month_number,
        d.month_name,
        d.quarter_number,
        d.quarter_name,
        d.week_of_year,
        d.day_name,
        d.is_weekend,
        d.is_holiday_season,

        COUNT(DISTINCT f.order_id)   AS orders,
        COUNT(DISTINCT f.customer_id) AS unique_customers,
        SUM(f.quantity)              AS units_sold,
        SUM(f.revenue)               AS total_revenue,
        SUM(f.gross_margin)          AS total_margin,
        SUM(f.cogs)                  AS total_cogs,
        SUM(f.discount_amount)       AS total_discounts,
        AVG(f.gross_margin_pct)      AS avg_margin_pct,
        AVG(f.revenue / NULLIF(f.quantity, 0)) AS avg_unit_selling_price

    FROM fct f
    JOIN dim_date d ON f.order_date = d.date_actual
    GROUP BY
        f.order_date, d.year_number, d.month_number, d.month_name,
        d.quarter_number, d.quarter_name, d.week_of_year,
        d.day_name, d.is_weekend, d.is_holiday_season
),

with_rolling AS (
    SELECT
        *,
        -- 7-day rolling average revenue
        AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS revenue_7d_avg,

        -- 30-day rolling average
        AVG(total_revenue) OVER (
            ORDER BY order_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS revenue_30d_avg,

        -- Week-over-week growth
        LAG(total_revenue, 7) OVER (ORDER BY order_date) AS revenue_7d_ago,
        ROUND(
            (total_revenue - LAG(total_revenue, 7) OVER (ORDER BY order_date))
            / NULLIF(LAG(total_revenue, 7) OVER (ORDER BY order_date), 0) * 100, 2
        ) AS wow_growth_pct,

        -- Cumulative revenue YTD
        SUM(total_revenue) OVER (
            PARTITION BY year_number
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS ytd_revenue

    FROM daily
)

SELECT * FROM with_rolling
ORDER BY order_date
