"""
Enterprise Retail Analytics Engine
Flask Application — Main Entry Point
Serves 5 pages: Dashboard, Revenue, Products, Customers, Ask Your Data
Connects to Snowflake with mock data fallback when credentials are unavailable
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from snowflake_connector import SnowflakeConnector
from gemini_sql_agent import GeminiSQLAgent

# ─── App Setup ────────────────────────────────────────────────────────────────

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "retail-analytics-secret-2024")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── Singletons ──────────────────────────────────────────────────────────────

sf = SnowflakeConnector()
agent = GeminiSQLAgent()


# ─── Mock Data ───────────────────────────────────────────────────────────────

def get_mock_kpi_data():
    return {
        "total_revenue": 8_247_193.42,
        "total_orders": 50_000,
        "unique_customers": 8_342,
        "avg_order_value": 164.94,
        "total_margin": 2_987_441.88,
        "avg_margin_pct": 36.22,
        "yoy_growth": 18.4,
    }


def get_mock_daily_revenue(days=90):
    import random
    random.seed(42)
    data = []
    base = datetime(2024, 10, 3)
    base_rev = 22_000
    for i in range(days):
        d = base + timedelta(days=i)
        rev = base_rev + random.gauss(0, 3000) + (i * 25)
        if d.weekday() in (5, 6):
            rev *= 1.3
        if d.month == 11:
            rev *= 1.5
        if d.month == 12:
            rev *= 1.8
        data.append({
            "date": d.strftime("%Y-%m-%d"),
            "revenue": round(max(rev, 5000), 2),
            "orders":  max(int(rev / 165), 30),
            "margin":  round(rev * 0.362, 2),
        })
    return data


def get_mock_category_data():
    return [
        {"category": "Electronics",  "revenue": 2_108_432, "margin_pct": 21.0, "orders": 12_104},
        {"category": "Clothing",     "revenue": 1_654_321, "margin_pct": 47.5, "orders": 14_230},
        {"category": "Home & Garden","revenue": 1_237_843, "margin_pct": 37.8, "orders": 9_876},
        {"category": "Sports",       "revenue": 987_654,  "margin_pct": 32.4, "orders": 7_654},
        {"category": "Books",        "revenue": 654_321,  "margin_pct": 42.1, "orders": 11_234},
        {"category": "Toys",         "revenue": 543_210,  "margin_pct": 42.8, "orders": 5_432},
        {"category": "Beauty",       "revenue": 498_765,  "margin_pct": 52.3, "orders": 4_321},
        {"category": "Food",         "revenue": 312_456,  "margin_pct": 30.1, "orders": 3_210},
        {"category": "Automotive",   "revenue": 154_321,  "margin_pct": 24.6, "orders": 987},
        {"category": "Office",       "revenue": 95_870,   "margin_pct": 37.2, "orders": 654},
    ]


def get_mock_top_products():
    return [
        {"rank": 1, "product_name": "Verizon Smart TV Pro",     "category": "Electronics", "revenue": 312_456, "margin_pct": 22.1, "units": 389},
        {"rank": 2, "product_name": "Nike Running Shoes Ultra", "category": "Clothing",    "revenue": 287_654, "margin_pct": 48.3, "units": 1_921},
        {"rank": 3, "product_name": "Dyson Vacuum Max",         "category": "Home & Garden","revenue": 265_432,"margin_pct": 28.7, "units": 331},
        {"rank": 4, "product_name": "Apple iPhone Elite",       "category": "Electronics", "revenue": 241_987, "margin_pct": 18.2, "units": 247},
        {"rank": 5, "product_name": "Levi's Jeans Premium",     "category": "Clothing",    "revenue": 198_765, "margin_pct": 51.2, "units": 3_054},
        {"rank": 6, "product_name": "Bowflex Dumbbells Pro",    "category": "Sports",      "revenue": 187_432, "margin_pct": 33.4, "units": 532},
        {"rank": 7, "product_name": "Sony Headphones Plus",     "category": "Electronics", "revenue": 176_543, "margin_pct": 24.8, "units": 504},
        {"rank": 8, "product_name": "Loreal Serum Ultra",       "category": "Beauty",      "revenue": 154_321, "margin_pct": 58.7, "units": 2_187},
        {"rank": 9, "product_name": "Python Handbook Elite",    "category": "Books",       "revenue": 143_210, "margin_pct": 44.3, "units": 3_182},
        {"rank":10, "product_name": "LEGO Master Set Plus",     "category": "Toys",        "revenue": 132_987, "margin_pct": 38.9, "units": 664},
    ]


def get_mock_top_customers():
    return [
        {"rank": 1, "full_name": "James Thornton",   "country": "United States", "rfm_segment": "Champions",      "ltv_tier": "Platinum", "lifetime_revenue": 15_432.87, "total_orders": 47, "avg_order_value": 328.36},
        {"rank": 2, "full_name": "Sarah Mitchell",   "country": "United Kingdom","rfm_segment": "Champions",      "ltv_tier": "Platinum", "lifetime_revenue": 13_987.54, "total_orders": 42, "avg_order_value": 332.80},
        {"rank": 3, "full_name": "Mohammed Al-Farsi","country": "United States", "rfm_segment": "Loyal Customers","ltv_tier": "Platinum", "lifetime_revenue": 12_654.32, "total_orders": 38, "avg_order_value": 333.01},
        {"rank": 4, "full_name": "Emily Chen",       "country": "Canada",        "rfm_segment": "Champions",      "ltv_tier": "Platinum", "lifetime_revenue": 11_987.65, "total_orders": 35, "avg_order_value": 342.50},
        {"rank": 5, "full_name": "Lucas Müller",     "country": "Germany",       "rfm_segment": "Loyal Customers","ltv_tier": "Gold",     "lifetime_revenue": 10_432.10, "total_orders": 31, "avg_order_value": 336.52},
        {"rank": 6, "full_name": "Priya Sharma",     "country": "India",         "rfm_segment": "Champions",      "ltv_tier": "Gold",     "lifetime_revenue": 9_876.54,  "total_orders": 29, "avg_order_value": 340.57},
        {"rank": 7, "full_name": "Oliver Johnson",   "country": "Australia",     "rfm_segment": "Loyal Customers","ltv_tier": "Gold",     "lifetime_revenue": 9_123.45,  "total_orders": 27, "avg_order_value": 337.90},
        {"rank": 8, "full_name": "Isabelle Dupont",  "country": "France",        "rfm_segment": "Potential Loyalists","ltv_tier":"Gold",  "lifetime_revenue": 8_765.43,  "total_orders": 25, "avg_order_value": 350.62},
        {"rank": 9, "full_name": "Raj Patel",        "country": "United States", "rfm_segment": "Loyal Customers","ltv_tier": "Gold",     "lifetime_revenue": 8_432.10,  "total_orders": 24, "avg_order_value": 351.34},
        {"rank":10, "full_name": "Anna Kowalski",    "country": "Germany",       "rfm_segment": "Loyal Customers","ltv_tier": "Silver",   "lifetime_revenue": 7_987.65,  "total_orders": 22, "avg_order_value": 363.07},
    ]


def get_mock_customer_growth():
    data = []
    for month in range(1, 13):
        data.append({
            "month": datetime(2024, month, 1).strftime("%b %Y"),
            "new_customers": 750 + (month * 18) + (100 if month >= 10 else 0),
        })
    return data


def get_mock_rfm_segments():
    return [
        {"segment": "Champions",          "count": 892},
        {"segment": "Loyal Customers",    "count": 1_543},
        {"segment": "Potential Loyalists","count": 1_287},
        {"segment": "New Customers",      "count": 2_104},
        {"segment": "Needs Attention",    "count": 987},
        {"segment": "At Risk",            "count": 654},
        {"segment": "Lost",               "count": 433},
        {"segment": "Cant Lose Them",     "count": 342},
    ]


def get_mock_competitor_data():
    return [
        {"category": "Electronics",  "price_index": 104.2, "avg_our_retail_price": 487.50, "avg_competitor_price": 467.82, "overpriced": 8,  "underpriced": 5,  "competitive": 4,  "pricing_health": "Medium Risk — Slightly Overpriced"},
        {"category": "Clothing",     "price_index": 97.8,  "avg_our_retail_price": 82.30,  "avg_competitor_price": 84.15,  "overpriced": 3,  "underpriced": 4,  "competitive": 2,  "pricing_health": "Healthy — Competitive Pricing"},
        {"category": "Home & Garden","price_index": 108.5, "avg_our_retail_price": 145.60, "avg_competitor_price": 134.19, "overpriced": 3,  "underpriced": 1,  "competitive": 1,  "pricing_health": "Medium Risk — Slightly Overpriced"},
        {"category": "Sports",       "price_index": 95.4,  "avg_our_retail_price": 198.40, "avg_competitor_price": 207.91, "overpriced": 2,  "underpriced": 4,  "competitive": 2,  "pricing_health": "Opportunity — Underpriced"},
        {"category": "Books",        "price_index": 92.1,  "avg_our_retail_price": 32.50,  "avg_competitor_price": 35.29,  "overpriced": 1,  "underpriced": 3,  "competitive": 0,  "pricing_health": "Opportunity — Underpriced"},
    ]


# ─── Data Loader ─────────────────────────────────────────────────────────────

def load_data(query: str, mock_fn, *args, **kwargs):
    """Try Snowflake; fall back to mock data."""
    if sf.is_connected():
        try:
            return sf.query(query)
        except Exception as exc:
            log.warning(f"Snowflake query failed, using mock: {exc}")
    return mock_fn(*args, **kwargs)


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/dashboard")
def dashboard():
    kpi = get_mock_kpi_data()
    if sf.is_connected():
        try:
            kpi_rows = sf.query("""
                SELECT
                    SUM(revenue)                AS total_revenue,
                    COUNT(DISTINCT order_id)    AS total_orders,
                    COUNT(DISTINCT customer_id) AS unique_customers,
                    AVG(revenue / NULLIF(quantity,0)) AS avg_order_value,
                    SUM(gross_margin)           AS total_margin,
                    AVG(gross_margin_pct)       AS avg_margin_pct
                FROM RETAIL_DW.MARTS.FCT_SALES
            """)
            if kpi_rows:
                row = kpi_rows[0]
                kpi = {
                    "total_revenue":    float(row.get("TOTAL_REVENUE", 0) or 0),
                    "total_orders":     int(row.get("TOTAL_ORDERS", 0) or 0),
                    "unique_customers": int(row.get("UNIQUE_CUSTOMERS", 0) or 0),
                    "avg_order_value":  float(row.get("AVG_ORDER_VALUE", 0) or 0),
                    "total_margin":     float(row.get("TOTAL_MARGIN", 0) or 0),
                    "avg_margin_pct":   float(row.get("AVG_MARGIN_PCT", 0) or 0),
                    "yoy_growth": 18.4,
                }
        except Exception as exc:
            log.warning(f"KPI query failed: {exc}")

    daily = get_mock_daily_revenue(30)
    categories = get_mock_category_data()
    return render_template("dashboard.html", kpi=kpi, daily=daily, categories=categories,
                           snowflake_live=sf.is_connected())


@app.route("/revenue")
def revenue():
    days = int(request.args.get("days", 365))
    daily = get_mock_daily_revenue(min(days, 365))
    categories = get_mock_category_data()

    if sf.is_connected():
        try:
            rows = sf.query(f"""
                SELECT order_date, SUM(revenue) AS revenue, COUNT(DISTINCT order_id) AS orders,
                       SUM(gross_margin) AS margin
                FROM RETAIL_DW.MARTS.FCT_SALES
                WHERE order_date >= DATEADD('day', -{days}, CURRENT_DATE())
                GROUP BY order_date
                ORDER BY order_date
            """)
            if rows:
                daily = [{"date": str(r["ORDER_DATE"]), "revenue": float(r["REVENUE"] or 0),
                          "orders": int(r["ORDERS"] or 0), "margin": float(r["MARGIN"] or 0)}
                         for r in rows]
        except Exception as exc:
            log.warning(f"Revenue query failed: {exc}")

    return render_template("revenue.html", daily=daily, categories=categories,
                           days=days, snowflake_live=sf.is_connected())


@app.route("/products")
def products():
    category_filter = request.args.get("category", "All")
    top_products = get_mock_top_products()
    competitor_data = get_mock_competitor_data()
    categories = [c["category"] for c in get_mock_category_data()]

    if sf.is_connected():
        try:
            top_products = sf.query("""
                SELECT margin_rank AS rank, product_name, category,
                       total_revenue AS revenue, avg_realized_margin_pct AS margin_pct,
                       total_units_sold AS units
                FROM RETAIL_DW.ANALYTICS.MOST_PROFITABLE_PRODUCTS
                ORDER BY margin_rank
                LIMIT 20
            """)
            top_products = [{k.lower(): v for k, v in dict(r).items()} for r in top_products]
        except Exception as exc:
            log.warning(f"Products query failed: {exc}")

    return render_template("products.html", top_products=top_products,
                           competitor_data=competitor_data, categories=categories,
                           category_filter=category_filter, snowflake_live=sf.is_connected())


@app.route("/customers")
def customers():
    top_customers = get_mock_top_customers()
    customer_growth = get_mock_customer_growth()
    rfm_segments = get_mock_rfm_segments()
    kpi = {
        "total_customers": 10_000,
        "active_customers": 7_234,
        "avg_ltv": 824.72,
        "champions_count": 892,
    }

    if sf.is_connected():
        try:
            top_customers = sf.query("""
                SELECT revenue_rank AS rank, full_name, country, rfm_segment, ltv_tier,
                       lifetime_revenue, total_orders, avg_order_value
                FROM RETAIL_DW.ANALYTICS.TOP_CUSTOMERS
                ORDER BY revenue_rank
                LIMIT 20
            """)
            top_customers = [{k.lower(): v for k, v in dict(r).items()} for r in top_customers]
        except Exception as exc:
            log.warning(f"Customers query failed: {exc}")

    return render_template("customers.html", top_customers=top_customers,
                           customer_growth=customer_growth, rfm_segments=rfm_segments,
                           kpi=kpi, snowflake_live=sf.is_connected())


@app.route("/ask-data", methods=["GET"])
def ask_data():
    example_questions = [
        "Show total revenue for the top 5 customers",
        "What are the highest margin products?",
        "Compare our prices with competitors by category",
        "Show monthly revenue trends for 2024",
        "Which customer segments generate the most revenue?",
        "List overpriced products vs competitors",
        "Show daily orders for the last 30 days",
        "What is the customer lifetime value by country?",
    ]
    return render_template("ask_data.html", example_questions=example_questions,
                           snowflake_live=sf.is_connected())


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """GenAI endpoint: NL question → SQL → results"""
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400
    if len(question) > 500:
        return jsonify({"error": "Question too long (max 500 chars)"}), 400

    try:
        # Step 1: Generate SQL via Gemini
        sql, explanation = agent.generate_sql(question)

        # Step 2: Validate SQL
        is_safe, safety_msg = agent.validate_sql(sql)
        if not is_safe:
            return jsonify({
                "question": question,
                "sql": sql,
                "error": f"SQL safety check failed: {safety_msg}",
                "results": [],
            }), 400

        # Step 3: Execute
        if sf.is_connected():
            rows = sf.query(sql)
            results = [dict(r) for r in rows]
            columns = list(results[0].keys()) if results else []
        else:
            # Demo mode: return mock results
            results, columns = agent.get_mock_results(question)

        return jsonify({
            "question":    question,
            "sql":         sql,
            "explanation": explanation,
            "columns":     columns,
            "results":     results,
            "row_count":   len(results),
            "live_data":   sf.is_connected(),
        })

    except Exception as exc:
        log.error(f"Ask Your Data error: {exc}")
        return jsonify({"error": str(exc), "question": question}), 500


@app.route("/api/revenue-chart")
def api_revenue_chart():
    days = int(request.args.get("days", 30))
    data = get_mock_daily_revenue(min(days, 365))
    return jsonify(data)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "snowflake_connected": sf.is_connected(),
        "gemini_configured": agent.is_configured(),
        "timestamp": datetime.utcnow().isoformat(),
    })


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    log.info(f"Starting Retail Analytics Engine on port {port}")
    log.info(f"Snowflake connected: {sf.is_connected()}")
    log.info(f"Gemini configured:   {agent.is_configured()}")
    app.run(host="0.0.0.0", port=port, debug=debug)
