-- models/marts/dim_customer.sql
-- Customer dimension — SCD Type 1 (latest snapshot)

{{ config(
    materialized = 'table',
    schema = 'marts',
    tags = ['marts', 'dimension']
) }}

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders_agg AS (
    SELECT
        o.customer_id,
        MIN(o.order_date)   AS first_order_date,
        MAX(o.order_date)   AS last_order_date,
        COUNT(o.order_id)   AS total_orders
    FROM {{ ref('stg_orders') }} o
    GROUP BY o.customer_id
),

final AS (
    SELECT
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['c.customer_id']) }}  AS customer_key,

        -- Natural key
        c.customer_id,

        -- Attributes
        c.first_name,
        c.last_name,
        c.full_name,
        c.gender,
        c.email,
        c.city,
        c.country,
        c.registration_date,

        -- Derived
        DATEDIFF('day', c.registration_date, CURRENT_DATE())       AS days_since_registration,

        -- From orders
        oa.first_order_date,
        oa.last_order_date,
        COALESCE(oa.total_orders, 0)                               AS lifetime_order_count,

        -- Customer tenure bucket
        CASE
            WHEN c.registration_date >= DATEADD('year', -1, CURRENT_DATE()) THEN 'New (< 1yr)'
            WHEN c.registration_date >= DATEADD('year', -3, CURRENT_DATE()) THEN 'Established (1-3yr)'
            ELSE 'Loyal (3yr+)'
        END AS tenure_segment,

        -- Activity status
        CASE
            WHEN oa.last_order_date >= DATEADD('day', -90, CURRENT_DATE())  THEN 'Active'
            WHEN oa.last_order_date >= DATEADD('day', -365, CURRENT_DATE()) THEN 'At Risk'
            WHEN oa.last_order_date IS NULL                                  THEN 'Never Ordered'
            ELSE 'Churned'
        END AS activity_status,

        CURRENT_TIMESTAMP() AS dw_created_at,
        CURRENT_TIMESTAMP() AS dw_updated_at

    FROM customers c
    LEFT JOIN orders_agg oa ON c.customer_id = oa.customer_id
)

SELECT * FROM final
