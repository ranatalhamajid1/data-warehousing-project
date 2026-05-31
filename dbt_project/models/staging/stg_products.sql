-- models/staging/stg_products.sql
-- Cleans, types, and enriches the raw products staging table

{{ config(
    materialized = 'view',
    schema = 'staging',
    tags = ['staging', 'products']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_products') }}
),

cleaned AS (
    SELECT
        TRIM(product_id)                              AS product_id,
        TRIM(product_name)                            AS product_name,
        TRIM(category)                                AS category,
        TRY_TO_DECIMAL(retail_price, 10, 2)           AS retail_price,
        TRY_TO_DECIMAL(base_cost, 10, 2)              AS base_cost,

        -- Computed margin metrics
        CASE
            WHEN TRY_TO_DECIMAL(retail_price, 10, 2) > 0
            THEN ROUND(
                (TRY_TO_DECIMAL(retail_price, 10, 2) - TRY_TO_DECIMAL(base_cost, 10, 2))
                / TRY_TO_DECIMAL(retail_price, 10, 2) * 100, 2
            )
            ELSE NULL
        END AS gross_margin_pct,

        -- Price tier classification
        CASE
            WHEN TRY_TO_DECIMAL(retail_price, 10, 2) < 25  THEN 'Budget'
            WHEN TRY_TO_DECIMAL(retail_price, 10, 2) < 100 THEN 'Mid-Range'
            WHEN TRY_TO_DECIMAL(retail_price, 10, 2) < 500 THEN 'Premium'
            ELSE 'Luxury'
        END AS price_tier,

        _loaded_at
    FROM source
    WHERE product_id IS NOT NULL
      AND TRIM(product_id) != ''
      AND TRY_TO_DECIMAL(retail_price, 10, 2) > 0
)

SELECT * FROM cleaned
