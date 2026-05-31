-- models/staging/stg_orders.sql
-- Cleans and enriches raw orders staging table

{{ config(
    materialized = 'view',
    schema = 'staging',
    tags = ['staging', 'orders']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_orders') }}
),

cleaned AS (
    SELECT
        TRIM(order_id)                              AS order_id,
        TRIM(customer_id)                           AS customer_id,
        order_date,

        -- Date part extractions for dimensional joins
        YEAR(order_date)                         AS order_year,
        MONTH(order_date)                        AS order_month,
        QUARTER(order_date)                      AS order_quarter,
        DAYOFWEEK(order_date)                    AS order_day_of_week,
        DAYNAME(order_date)                      AS order_day_name,
        MONTHNAME(order_date)                    AS order_month_name,
        DATE_TRUNC('week', order_date)           AS order_week_start,

        _loaded_at
    FROM source
    WHERE order_id IS NOT NULL
      AND TRIM(order_id) != ''
      AND order_date IS NOT NULL
)

SELECT * FROM cleaned
