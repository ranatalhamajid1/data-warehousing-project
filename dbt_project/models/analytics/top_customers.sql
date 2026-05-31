-- models/analytics/top_customers.sql
-- Top customers by revenue with ranking and segmentation

{{ config(
    materialized = 'table',
    schema = 'analytics',
    tags = ['analytics', 'customers']
) }}

WITH ltv AS (
    SELECT * FROM {{ ref('customer_ltv') }}
),

ranked AS (
    SELECT
        *,
        RANK()   OVER (ORDER BY historical_ltv DESC) AS overall_revenue_rank,
        RANK()   OVER (ORDER BY total_orders DESC)   AS order_frequency_rank,
        RANK()   OVER (ORDER BY avg_order_value DESC) AS aov_rank,

        -- Percentile
        PERCENT_RANK() OVER (ORDER BY historical_ltv ASC) AS revenue_percentile

    FROM ltv
),

final AS (
    SELECT
        overall_revenue_rank  AS revenue_rank,
        customer_id,
        full_name,
        country,
        city,
        gender,
        tenure_segment,
        activity_status,
        registration_date,
        first_order_date,
        last_order_date,
        days_since_last_order,

        total_orders,
        total_units,
        ROUND(historical_ltv, 2)          AS lifetime_revenue,
        ROUND(total_margin, 2)            AS lifetime_margin,
        ROUND(avg_order_value, 2)         AS avg_order_value,
        ROUND(predicted_annual_ltv, 2)    AS predicted_annual_ltv,

        rfm_segment,
        ltv_tier,
        recency_score,
        frequency_score,
        monetary_score,
        rfm_total_score,

        ROUND(revenue_percentile * 100, 1) AS revenue_percentile,
        order_frequency_rank,
        aov_rank,

        -- Top 10 / Top 100 flags
        IFF(overall_revenue_rank <= 10,  TRUE, FALSE) AS is_top_10,
        IFF(overall_revenue_rank <= 100, TRUE, FALSE) AS is_top_100,

        customer_lifespan_days

    FROM ranked
)

SELECT * FROM final
ORDER BY revenue_rank
