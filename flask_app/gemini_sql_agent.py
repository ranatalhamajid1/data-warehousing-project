"""
Enterprise Retail Analytics Engine
Gemini SQL Agent — GenAI Natural Language to SQL Interface
Converts natural language questions to validated, safe Snowflake SQL queries
Uses Google Gemini API with prompt engineering and SQL guardrails
"""

import os
import re
import logging
from typing import Tuple, List, Dict, Any

log = logging.getLogger(__name__)

# ─── Schema Context ───────────────────────────────────────────────────────────

SCHEMA_CONTEXT = """
You are an expert SQL analyst for a retail analytics data warehouse in Snowflake.
The database is RETAIL_DW with the following schemas and tables:

== MARTS Schema (Dimensional Model) ==

RETAIL_DW.MARTS.FCT_SALES (fact table — one row per order line item):
  - sales_key (VARCHAR) — surrogate key
  - customer_key, product_key, date_key — FK to dimensions
  - order_id, order_item_id, customer_id, product_id (VARCHAR)
  - order_date (DATE)
  - category (VARCHAR) — Electronics, Clothing, Home & Garden, Sports, Books, Toys, Beauty, Food, Automotive, Office
  - quantity (INT)
  - unit_price (NUMBER) — actual selling price
  - revenue (NUMBER) — quantity × unit_price
  - cogs (NUMBER) — cost of goods sold
  - gross_margin (NUMBER) — revenue - cogs
  - gross_margin_pct (NUMBER) — margin as percentage
  - discount_amount (NUMBER)
  - discount_pct (NUMBER)
  - competitor_price_delta (NUMBER) — our price minus avg competitor price (NULL if no data)
  - competitive_position (VARCHAR)

RETAIL_DW.MARTS.DIM_CUSTOMER:
  - customer_key, customer_id, full_name, first_name, last_name
  - gender, email, city, country, registration_date
  - tenure_segment, activity_status, lifetime_order_count

RETAIL_DW.MARTS.DIM_PRODUCT:
  - product_key, product_id, product_name, category
  - retail_price, base_cost, gross_margin_pct, price_tier
  - competitive_position, avg_competitor_price, price_vs_avg_competitor

RETAIL_DW.MARTS.DIM_DATE:
  - date_key, date_actual, year_number, quarter_number, month_number
  - month_name, week_of_year, day_name, is_weekend, is_holiday_season

== ANALYTICS Schema (Pre-aggregated) ==

RETAIL_DW.ANALYTICS.DAILY_REVENUE:
  - order_date, year_number, month_number, month_name, quarter_name
  - orders, unique_customers, units_sold, total_revenue, total_margin
  - avg_margin_pct, revenue_7d_avg, revenue_30d_avg, wow_growth_pct, ytd_revenue

RETAIL_DW.ANALYTICS.TOP_CUSTOMERS:
  - revenue_rank, customer_id, full_name, country, city
  - rfm_segment, ltv_tier, total_orders, lifetime_revenue, avg_order_value
  - is_top_10, is_top_100, recency_score, frequency_score, monetary_score

RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS:
  - margin_rank, revenue_rank, product_id, product_name, category
  - total_revenue, total_gross_margin, avg_realized_margin_pct
  - competitive_position, avg_competitor_price, avg_competitor_delta
  - performance_label, total_units_sold, times_ordered

RETAIL_DW.ANALYTICS.CUSTOMER_LTV:
  - customer_id, full_name, country, rfm_segment, ltv_tier
  - historical_ltv, predicted_annual_ltv, total_orders, avg_order_value
  - recency_score, frequency_score, monetary_score, rfm_total_score

RETAIL_DW.ANALYTICS.COMPETITOR_PRICING_INDEX:
  - category, price_index, avg_our_retail_price, avg_competitor_price
  - overpriced_count, underpriced_count, competitive_count, pricing_health
  - total_revenue

RETAIL_DW.ANALYTICS.TOP_CATEGORIES:
  - category, month_start, total_revenue, total_margin, orders
  - avg_margin_pct, revenue_rank, mom_growth_pct

== Rules ==
- Always use fully-qualified table names (RETAIL_DW.schema.table)
- Only generate SELECT statements — never INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE
- Limit results to 1000 rows maximum with LIMIT clause
- Use Snowflake-compatible SQL syntax
- For date math use DATEADD and DATEDIFF
- Always include ORDER BY for ranked queries
- Format monetary values with ROUND(..., 2)
"""

SAFE_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|CALL|MERGE)\b",
    re.IGNORECASE,
)

SQL_INJECTION_PATTERNS = [
    r"--",
    r"/\*.*?\*/",
    r";\s*(DROP|INSERT|DELETE|UPDATE|CREATE|ALTER)",
    r"UNION\s+ALL\s+SELECT.*(password|passwd|secret|token|key)",
    r"xp_cmdshell",
    r"INFORMATION_SCHEMA\.(COLUMNS|TABLES|SCHEMATA)",
]


# ─── Agent ────────────────────────────────────────────────────────────────────

class GeminiSQLAgent:
    """
    Natural language → SQL agent powered by Google Gemini.
    Includes prompt engineering, SQL validation, injection protection.
    """

    def __init__(self):
        self._model = None
        self._configured = False
        self._api_key = os.environ.get("GEMINI_API_KEY", "")
        self._model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self._init_client()

    def _init_client(self):
        if not self._api_key:
            log.warning("GEMINI_API_KEY not set — running in demo mode")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                model_name=self._model_name,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "max_output_tokens": 2048,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ],
            )
            self._configured = True
            log.info(f"[OK] Gemini configured: {self._model_name}")
        except Exception as exc:
            log.warning(f"Gemini init failed (demo mode): {exc}")

    def is_configured(self) -> bool:
        return self._configured

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL for safety:
        1. No DML/DDL operations
        2. No SQL injection patterns
        3. Must be a SELECT statement
        4. Reasonable length
        """
        sql_upper = sql.strip().upper()

        # Must start with SELECT
        if not sql_upper.lstrip().startswith("SELECT"):
            return False, "Only SELECT statements are allowed"

        # Check for DML/DDL keywords
        match = SAFE_SQL_PATTERN.search(sql)
        if match:
            return False, f"Forbidden SQL keyword: {match.group()}"

        # Check injection patterns
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
                return False, f"Potential SQL injection pattern detected"

        # Length sanity check
        if len(sql) > 5000:
            return False, "Generated SQL is too long (max 5000 chars)"

        # Must reference our database
        if "RETAIL_DW" not in sql.upper() and "FCT_SALES" not in sql.upper() \
                and "DIM_" not in sql.upper() and "ANALYTICS" not in sql.upper():
            return False, "SQL must reference the RETAIL_DW database tables"

        return True, "OK"

    def generate_sql(self, question: str) -> Tuple[str, str]:
        """
        Convert a natural language question to a SQL query.
        Returns (sql_string, explanation_string).
        Falls back to rule-based generation if Gemini is unavailable.
        """
        if not self._configured:
            return self._rule_based_sql(question)

        prompt = f"""
{SCHEMA_CONTEXT}

== Task ==
Convert the following business question into a Snowflake SQL SELECT query.

Question: "{question}"

== Output Format (STRICT) ==
Return ONLY a JSON object with exactly these two fields:
{{
  "sql": "SELECT ... FROM ...",
  "explanation": "Brief description of what the query returns"
}}

Do NOT include markdown code blocks, comments, or any text outside the JSON.
The SQL must be production-ready, safe, and limited to 1000 rows maximum.
"""

        try:
            response = self._model.generate_content(prompt)
            text = response.text.strip()

            # Strip markdown code fences if present
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

            import json
            parsed = json.loads(text)
            sql = parsed.get("sql", "").strip()
            explanation = parsed.get("explanation", "Query generated by Gemini AI")

            if not sql:
                raise ValueError("Empty SQL returned")

            # Enforce LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = sql.rstrip(";") + "\nLIMIT 1000"

            return sql, explanation

        except Exception as exc:
            log.warning(f"Gemini generation failed: {exc}. Falling back to rule-based.")
            return self._rule_based_sql(question)

    def _rule_based_sql(self, question: str) -> Tuple[str, str]:
        """
        Fallback rule-based SQL generation for demo mode.
        Maps common question patterns to pre-built queries.
        """
        q = question.lower()

        if any(w in q for w in ["top 5 customer", "top five customer", "best customer",
                                  "highest revenue customer"]):
            sql = """
SELECT revenue_rank, full_name, country, rfm_segment, ltv_tier,
       ROUND(lifetime_revenue, 2) AS lifetime_revenue,
       total_orders, ROUND(avg_order_value, 2) AS avg_order_value
FROM RETAIL_DW.ANALYTICS.TOP_CUSTOMERS
ORDER BY revenue_rank
LIMIT 5"""
            return sql.strip(), "Top 5 customers ranked by lifetime revenue"

        if any(w in q for w in ["monthly revenue", "revenue by month", "monthly sales"]):
            sql = """
SELECT year_number, month_number, month_name,
       SUM(orders) AS monthly_orders,
       ROUND(SUM(total_revenue), 2) AS monthly_revenue,
       ROUND(SUM(total_margin), 2) AS monthly_margin,
       ROUND(AVG(avg_margin_pct), 2) AS avg_margin_pct
FROM RETAIL_DW.ANALYTICS.DAILY_REVENUE
GROUP BY year_number, month_number, month_name
ORDER BY year_number, month_number
LIMIT 12"""
            return sql.strip(), "Monthly revenue trends for 2024"

        if any(w in q for w in ["highest margin", "most profitable", "best margin"]):
            sql = """
SELECT margin_rank, product_name, category,
       ROUND(avg_realized_margin_pct, 1) AS margin_pct,
       ROUND(total_gross_margin, 2) AS total_margin,
       total_units_sold,
       ROUND(total_revenue, 2) AS revenue
FROM RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS
ORDER BY margin_pct_rank
LIMIT 10"""
            return sql.strip(), "Top 10 products by gross margin percentage"

        if any(w in q for w in ["category", "best category", "category performance", "top category"]):
            sql = """
SELECT category,
       SUM(orders) AS total_orders,
       ROUND(SUM(total_revenue), 2) AS total_revenue,
       ROUND(SUM(total_margin), 2) AS total_margin,
       ROUND(AVG(avg_margin_pct), 2) AS avg_margin_pct,
       revenue_rank
FROM RETAIL_DW.ANALYTICS.TOP_CATEGORIES
GROUP BY category, revenue_rank
ORDER BY revenue_rank
LIMIT 10"""
            return sql.strip(), "Category performance ranked by total revenue"

        if any(w in q for w in ["competitor", "overpriced", "underpriced", "price comparison"]):
            sql = """
SELECT category, price_index,
       ROUND(avg_our_retail_price, 2) AS avg_our_price,
       ROUND(avg_competitor_price, 2) AS avg_comp_price,
       overpriced_count, underpriced_count, competitive_count,
       pricing_health
FROM RETAIL_DW.ANALYTICS.COMPETITOR_PRICING_INDEX
ORDER BY price_index DESC
LIMIT 20"""
            return sql.strip(), "Competitive pricing analysis by category"

        if any(w in q for w in ["customer segment", "rfm", "segment", "loyal", "champion"]):
            sql = """
SELECT rfm_segment, ltv_tier,
       COUNT(*) AS customer_count,
       ROUND(AVG(historical_ltv), 2) AS avg_ltv,
       ROUND(SUM(historical_ltv), 2) AS total_ltv,
       ROUND(AVG(total_orders), 1) AS avg_orders
FROM RETAIL_DW.ANALYTICS.CUSTOMER_LTV
GROUP BY rfm_segment, ltv_tier
ORDER BY total_ltv DESC
LIMIT 20"""
            return sql.strip(), "Customer RFM segmentation summary"

        if any(w in q for w in ["daily", "day", "last 30", "recent"]):
            sql = """
SELECT order_date, orders,
       ROUND(total_revenue, 2) AS revenue,
       ROUND(total_margin, 2) AS margin,
       ROUND(revenue_7d_avg, 2) AS rolling_7d_avg
FROM RETAIL_DW.ANALYTICS.DAILY_REVENUE
WHERE order_date >= DATEADD('day', -30, CURRENT_DATE())
ORDER BY order_date DESC
LIMIT 30"""
            return sql.strip(), "Daily revenue for the last 30 days"

        # Default: general revenue summary
        sql = """
SELECT
    COUNT(DISTINCT order_id)    AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(quantity)               AS total_units,
    ROUND(SUM(revenue), 2)      AS total_revenue,
    ROUND(SUM(gross_margin), 2) AS total_margin,
    ROUND(AVG(gross_margin_pct), 2) AS avg_margin_pct
FROM RETAIL_DW.MARTS.FCT_SALES
LIMIT 1"""
        return sql.strip(), "Overall sales performance summary"

    def get_mock_results(self, question: str) -> Tuple[List[Dict], List[str]]:
        """Return demo results when neither Gemini nor Snowflake are connected."""
        q = question.lower()

        if "top 5 customer" in q or "best customer" in q:
            results = [
                {"revenue_rank": 1, "full_name": "James Thornton",   "country": "United States", "lifetime_revenue": 15432.87, "total_orders": 47},
                {"revenue_rank": 2, "full_name": "Sarah Mitchell",   "country": "United Kingdom","lifetime_revenue": 13987.54, "total_orders": 42},
                {"revenue_rank": 3, "full_name": "Emily Chen",       "country": "Canada",        "lifetime_revenue": 12654.32, "total_orders": 38},
                {"revenue_rank": 4, "full_name": "Mohammed Al-Farsi","country": "United States", "lifetime_revenue": 11987.65, "total_orders": 35},
                {"revenue_rank": 5, "full_name": "Lucas Müller",     "country": "Germany",       "lifetime_revenue": 10432.10, "total_orders": 31},
            ]
            return results, list(results[0].keys())

        if "monthly revenue" in q:
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            revenues = [521000, 498000, 612000, 587000, 634000, 671000,
                        695000, 712000, 698000, 743000, 912000, 964193]
            results = [
                {"month_name": m, "month_number": i+1,
                 "monthly_revenue": r, "avg_margin_pct": 36.2}
                for i, (m, r) in enumerate(zip(months, revenues))
            ]
            return results, list(results[0].keys())

        # Default summary
        results = [{"total_orders": 50000, "unique_customers": 8342,
                    "total_revenue": 8247193.42, "avg_margin_pct": 36.22}]
        return results, list(results[0].keys())
