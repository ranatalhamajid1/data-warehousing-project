-- models/marts/dim_date.sql
-- Full date dimension — covers 2024 calendar year + 2 years buffer

{{ config(
    materialized = 'table',
    schema = 'marts',
    tags = ['marts', 'dimension']
) }}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart = "day",
        start_date = "cast('2023-01-01' as date)",
        end_date = "cast('2026-12-31' as date)"
    ) }}
),

final AS (
    SELECT
        -- Surrogate key
        TO_NUMBER(TO_CHAR(date_day, 'YYYYMMDD'))   AS date_key,

        -- Natural key
        date_day                                    AS date_actual,

        -- Year / Quarter / Month
        YEAR(date_day)                              AS year_number,
        QUARTER(date_day)                           AS quarter_number,
        'Q' || QUARTER(date_day)                   AS quarter_name,
        CONCAT(YEAR(date_day), '-Q', QUARTER(date_day)) AS year_quarter,
        MONTH(date_day)                             AS month_number,
        MONTHNAME(date_day)                         AS month_name,
        LEFT(MONTHNAME(date_day), 3)               AS month_short_name,
        CONCAT(YEAR(date_day), '-', LPAD(MONTH(date_day), 2, '0')) AS year_month,

        -- Week
        WEEKOFYEAR(date_day)                        AS week_of_year,
        DATE_TRUNC('week', date_day)               AS week_start_date,
        DATEADD('day', 6, DATE_TRUNC('week', date_day)) AS week_end_date,

        -- Day
        DAY(date_day)                               AS day_of_month,
        DAYOFWEEK(date_day)                         AS day_of_week,
        DAYOFYEAR(date_day)                         AS day_of_year,
        DAYNAME(date_day)                           AS day_name,
        LEFT(DAYNAME(date_day), 3)                 AS day_short_name,

        -- Flags
        IFF(DAYOFWEEK(date_day) IN (0, 6), TRUE, FALSE)  AS is_weekend,
        IFF(DAYOFWEEK(date_day) IN (1, 2, 3, 4, 5), TRUE, FALSE) AS is_weekday,
        IFF(date_day = LAST_DAY(date_day), TRUE, FALSE)  AS is_last_day_of_month,
        IFF(date_day = DATE_TRUNC('month', date_day), TRUE, FALSE) AS is_first_day_of_month,

        -- Retail calendar helpers
        CASE MONTH(date_day)
            WHEN 11 THEN TRUE
            WHEN 12 THEN TRUE
            ELSE FALSE
        END AS is_holiday_season,

        -- Relative
        DATEDIFF('day', date_day, CURRENT_DATE())  AS days_ago,
        IFF(date_day <= CURRENT_DATE(), TRUE, FALSE) AS is_historical

    FROM date_spine
)

SELECT * FROM final
