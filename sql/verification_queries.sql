-- sql/verification_queries.sql
-- Business intelligence verification queries
-- Run these in Snowflake after dbt models are built

-- ─── 1. Overpriced Products (we charge more than competitors) ────────────────

SELECT
    product_name,
    category,
    retail_price,
    avg_competitor_price,
    ROUND(retail_price - avg_competitor_price, 2)  AS price_premium_usd,
    ROUND((retail_price - avg_competitor_price) / avg_competitor_price * 100, 1) AS price_premium_pct,
    competitive_position,
    total_revenue,
    avg_realized_margin_pct
FROM RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS
WHERE competitive_position = 'Overpriced'
ORDER BY price_premium_usd DESC
LIMIT 20;

-- ─── 2. Underpriced Products (opportunity to raise prices) ───────────────────

SELECT
    product_name,
    category,
    retail_price,
    avg_competitor_price,
    ROUND(avg_competitor_price - retail_price, 2)  AS opportunity_usd,
    ROUND((avg_competitor_price - retail_price) / avg_competitor_price * 100, 1) AS opportunity_pct,
    total_units_sold,
    total_revenue,
    avg_realized_margin_pct
FROM RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS
WHERE competitive_position = 'Underpriced'
ORDER BY opportunity_usd DESC
LIMIT 20;

-- ─── 3. Highest Margin Products ──────────────────────────────────────────────

SELECT
    margin_rank,
    product_name,
    category,
    price_tier,
    ROUND(avg_realized_margin_pct, 1) AS margin_pct,
    ROUND(total_gross_margin, 2)      AS total_margin_usd,
    total_units_sold,
    ROUND(total_revenue, 2)           AS total_revenue,
    performance_label
FROM RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS
ORDER BY margin_pct_rank
LIMIT 25;

-- ─── 4. Customer Segmentation Summary ────────────────────────────────────────

SELECT
    rfm_segment,
    ltv_tier,
    COUNT(*)                                AS customer_count,
    ROUND(AVG(historical_ltv), 2)           AS avg_ltv,
    ROUND(SUM(historical_ltv), 2)           AS total_ltv,
    ROUND(AVG(total_orders), 1)             AS avg_orders,
    ROUND(AVG(avg_order_value), 2)          AS avg_order_value,
    ROUND(AVG(days_since_last_order), 0)    AS avg_recency_days
FROM RETAIL_DW.ANALYTICS.CUSTOMER_LTV
GROUP BY rfm_segment, ltv_tier
ORDER BY total_ltv DESC;

-- ─── 5. Competitive Pricing Health by Category ───────────────────────────────

SELECT
    category,
    products_tracked,
    ROUND(avg_our_retail_price, 2) AS avg_our_price,
    ROUND(avg_competitor_price, 2) AS avg_comp_price,
    ROUND(avg_price_delta, 2)      AS avg_delta,
    price_index,
    overpriced_count,
    underpriced_count,
    competitive_count,
    pricing_health,
    ROUND(total_revenue, 2)        AS total_revenue
FROM RETAIL_DW.ANALYTICS.COMPETITOR_PRICING_INDEX
ORDER BY price_index DESC;

-- ─── 6. Monthly Revenue Trend ────────────────────────────────────────────────

SELECT
    year_number,
    month_number,
    month_name,
    SUM(orders)              AS monthly_orders,
    SUM(unique_customers)    AS monthly_unique_customers,
    ROUND(SUM(total_revenue), 2) AS monthly_revenue,
    ROUND(SUM(total_margin), 2)  AS monthly_margin,
    ROUND(AVG(avg_margin_pct), 2) AS avg_margin_pct,
    ROUND(AVG(revenue_7d_avg), 2) AS avg_daily_7d_rolling
FROM RETAIL_DW.ANALYTICS.DAILY_REVENUE
GROUP BY year_number, month_number, month_name
ORDER BY year_number, month_number;

-- ─── 7. Top 10 Customers by Revenue ─────────────────────────────────────────

SELECT
    revenue_rank,
    full_name,
    country,
    city,
    rfm_segment,
    ltv_tier,
    total_orders,
    ROUND(lifetime_revenue, 2)   AS lifetime_revenue,
    ROUND(lifetime_margin, 2)    AS lifetime_margin,
    ROUND(avg_order_value, 2)    AS avg_order_value,
    days_since_last_order,
    activity_status
FROM RETAIL_DW.ANALYTICS.TOP_CUSTOMERS
WHERE is_top_10 = TRUE
ORDER BY revenue_rank;

-- ─── 8. Star Schema Row Count Verification ───────────────────────────────────

SELECT 'dim_customer'    AS model, COUNT(*) AS rows FROM RETAIL_DW.MARTS.DIM_CUSTOMER
UNION ALL
SELECT 'dim_product',    COUNT(*) FROM RETAIL_DW.MARTS.DIM_PRODUCT
UNION ALL
SELECT 'dim_date',       COUNT(*) FROM RETAIL_DW.MARTS.DIM_DATE
UNION ALL
SELECT 'fct_sales',      COUNT(*) FROM RETAIL_DW.MARTS.FCT_SALES
ORDER BY model;

-- ─── 9. Revenue by Quarter ───────────────────────────────────────────────────

SELECT
    year_number,
    quarter_name,
    SUM(orders)                   AS orders,
    ROUND(SUM(total_revenue), 2)  AS revenue,
    ROUND(SUM(total_margin), 2)   AS margin,
    ROUND(AVG(avg_margin_pct), 2) AS avg_margin_pct
FROM RETAIL_DW.ANALYTICS.DAILY_REVENUE
GROUP BY year_number, quarter_number, quarter_name
ORDER BY year_number, quarter_number;

-- ─── 10. Category Revenue Share ──────────────────────────────────────────────

SELECT
    category,
    SUM(orders)                                              AS total_orders,
    SUM(total_revenue)                                       AS total_revenue,
    ROUND(SUM(total_revenue) / SUM(SUM(total_revenue)) OVER () * 100, 2) AS revenue_share_pct,
    SUM(total_margin)                                        AS total_margin,
    ROUND(AVG(avg_margin_pct), 2)                            AS avg_margin_pct,
    revenue_rank
FROM RETAIL_DW.ANALYTICS.TOP_CATEGORIES
GROUP BY category, revenue_rank
ORDER BY revenue_rank;
