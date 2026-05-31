-- models/staging/stg_competitor_prices.sql
-- Cleans and enriches raw competitor price data

{{ config(
    materialized = 'view',
    schema = 'staging',
    tags = ['staging', 'competitor']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_competitor_prices') }}
),

cleaned AS (
    SELECT
        scraped_at,
        TRIM(category)                                AS category,
        TRIM(product_name)                            AS product_name,
        TRIM(competitor_name)                         AS competitor_name,
        competitor_price_usd,
        our_price_usd,
        TRIM(price_position)                          AS price_position,
        last_updated,
        price_delta_usd,
        price_delta_pct,

        -- Competitiveness flag
        CASE
            WHEN price_delta_usd > 5  THEN 'Overpriced'
            WHEN price_delta_usd < -5 THEN 'Underpriced'
            ELSE 'Competitive'
        END AS competitiveness_flag,

        _loaded_at
    FROM source
    WHERE product_name IS NOT NULL
      AND TRIM(product_name) != ''
)

SELECT * FROM cleaned
