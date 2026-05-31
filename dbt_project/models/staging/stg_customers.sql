-- models/staging/stg_customers.sql
-- Cleans and types the raw customers staging table

{{ config(
    materialized = 'view',
    schema = 'staging',
    tags = ['staging', 'customers']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_customers') }}
),

cleaned AS (
    SELECT
        TRIM(customer_id)                          AS customer_id,
        INITCAP(TRIM(first_name))                  AS first_name,
        INITCAP(TRIM(last_name))                   AS last_name,
        CONCAT(INITCAP(TRIM(first_name)), ' ', INITCAP(TRIM(last_name))) AS full_name,
        TRIM(gender)                               AS gender,
        LOWER(TRIM(email))                         AS email,
        INITCAP(TRIM(city))                        AS city,
        INITCAP(TRIM(country))                     AS country,
        registration_date,
        _loaded_at
    FROM source
    WHERE customer_id IS NOT NULL
      AND TRIM(customer_id) != ''
)

SELECT * FROM cleaned
