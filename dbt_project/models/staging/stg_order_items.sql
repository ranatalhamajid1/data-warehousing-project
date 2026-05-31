-- models/staging/stg_order_items.sql
-- Cleans and enriches raw order_items staging table

{{ config(
    materialized = 'view',
    schema = 'staging',
    tags = ['staging', 'order_items']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_order_items') }}
),

cleaned AS (
    SELECT
        TRIM(order_item_id)                           AS order_item_id,
        TRIM(order_id)                                AS order_id,
        TRIM(product_id)                              AS product_id,
        quantity::INT                                 AS quantity,
        unit_price                                    AS unit_price,

        -- Revenue line metric
        quantity * unit_price                         AS line_revenue,

        _loaded_at
    FROM source
    WHERE order_item_id IS NOT NULL
      AND TRIM(order_item_id) != ''
      AND quantity > 0
      AND unit_price > 0
)

SELECT * FROM cleaned
