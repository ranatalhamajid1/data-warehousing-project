-- models/analytics/customer_ltv.sql
-- Customer Lifetime Value analytics

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics', 'customers']
) }}

WITH fct AS (
    SELECT * FROM {{ ref('fct_sales') }}
),

dim_customer AS (
    SELECT * FROM {{ ref('dim_customer') }}
),

customer_sales AS (
    SELECT
        f.customer_id,
        COUNT(DISTINCT f.order_id)       AS total_orders,
        SUM(f.revenue)                   AS total_revenue,
        SUM(f.gross_margin)              AS total_margin,
        SUM(f.quantity)                  AS total_units,
        AVG(f.revenue / NULLIF(f.quantity, 0)) AS avg_unit_price,

        -- Order value stats
        AVG(order_totals.order_revenue)  AS avg_order_value,
        MIN(order_totals.order_revenue)  AS min_order_value,
        MAX(order_totals.order_revenue)  AS max_order_value,

        -- Time-based
        MIN(f.order_date)                AS first_order_date,
        MAX(f.order_date)                AS last_order_date,
        DATEDIFF('day', MIN(f.order_date), MAX(f.order_date)) AS customer_lifespan_days,

        -- Recency
        DATEDIFF('day', MAX(f.order_date), CURRENT_DATE()) AS days_since_last_order

    FROM fct f
    JOIN (
        SELECT order_id, SUM(revenue) AS order_revenue
        FROM fct
        GROUP BY order_id
    ) order_totals ON f.order_id = order_totals.order_id
    GROUP BY f.customer_id
),

with_ltv AS (
    SELECT
        cs.*,
        dc.full_name,
        dc.country,
        dc.city,
        dc.gender,
        dc.tenure_segment,
        dc.activity_status,
        dc.registration_date,

        -- LTV = Total Revenue (historical)
        cs.total_revenue AS historical_ltv,

        -- Predicted LTV (simplified): avg_order_value × estimated_future_orders
        -- Future orders estimated from purchase frequency and 12-month window
        CASE
            WHEN cs.customer_lifespan_days > 0
            THEN ROUND(
                cs.avg_order_value
                * (cs.total_orders / (cs.customer_lifespan_days / 365.0))
                * 1.0  -- 1 more year projected
            , 2)
            ELSE cs.avg_order_value
        END AS predicted_annual_ltv,

        -- RFM Scoring
        NTILE(5) OVER (ORDER BY DATEDIFF('day', cs.last_order_date, CURRENT_DATE()) ASC)  AS recency_score,
        NTILE(5) OVER (ORDER BY cs.total_orders ASC)                                       AS frequency_score,
        NTILE(5) OVER (ORDER BY cs.total_revenue ASC)                                      AS monetary_score

    FROM customer_sales cs
    JOIN dim_customer dc ON cs.customer_id = dc.customer_id
),

with_segments AS (
    SELECT
        *,
        (recency_score + frequency_score + monetary_score) AS rfm_total_score,

        -- RFM Segment
        CASE
            WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
            WHEN recency_score >= 3 AND frequency_score >= 3                          THEN 'Loyal Customers'
            WHEN recency_score >= 4 AND frequency_score <= 2                          THEN 'New Customers'
            WHEN recency_score >= 3 AND monetary_score >= 4                           THEN 'Potential Loyalists'
            WHEN recency_score <= 2 AND frequency_score >= 3 AND monetary_score >= 3  THEN 'At Risk'
            WHEN recency_score <= 2 AND frequency_score >= 4                          THEN 'Cant Lose Them'
            WHEN recency_score <= 1                                                   THEN 'Lost'
            ELSE 'Needs Attention'
        END AS rfm_segment,

        -- LTV tier
        NTILE(4) OVER (ORDER BY total_revenue ASC) AS ltv_quartile

    FROM with_ltv
)

SELECT
    *,
    CASE ltv_quartile
        WHEN 4 THEN 'Platinum'
        WHEN 3 THEN 'Gold'
        WHEN 2 THEN 'Silver'
        ELSE 'Bronze'
    END AS ltv_tier
FROM with_segments
ORDER BY historical_ltv DESC
