# 🏪 Enterprise Retail Analytics Engine

> A complete end-to-end retail analytics platform built with **Python**, **Snowflake**, **dbt**, and **Flask** — featuring a GenAI natural language query interface powered by **Google Gemini**.

---

## 📁 Project Structure

```
data-warehousing-project/
├── data/                          # Generated CSV datasets (auto-created)
│   ├── customers.csv              # 10,000 customer records
│   ├── products.csv               # 500 product catalog records
│   ├── orders.csv                 # 50,000 transaction records
│   ├── order_items.csv            # 150,000 line item records
│   └── competitor_prices.csv      # Web-scraped competitor pricing
│
├── etl/
│   ├── generate_data.py           # Part 1: Synthetic data generator
│   ├── snowflake_setup.sql        # Part 1: DDL — warehouse, DB, schemas, tables
│   └── load_to_snowflake.py       # Part 1: Pandas → Snowflake ETL loader
│
├── scraper/
│   ├── competitor_products.html   # Sample competitor price catalog
│   └── scraper.py                 # BeautifulSoup price extractor
│
├── dbt_project/
│   ├── dbt_project.yml            # dbt configuration
│   ├── profiles.yml               # Snowflake connection profile
│   ├── models/
│   │   ├── staging/               # 5 staging models (views)
│   │   ├── marts/                 # 4 dimensional models (tables)
│   │   ├── analytics/             # 6 pre-aggregated analytics models
│   │   └── schema.yml             # Tests: unique, not_null, relationships
│   └── macros/
│       └── generate_schema_name.sql
│
├── flask_app/
│   ├── app.py                     # Part 3: Flask application
│   ├── gemini_sql_agent.py        # GenAI SQL generation engine
│   ├── snowflake_connector.py     # Snowflake connection manager
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variable template
│   ├── static/
│   │   ├── css/style.css          # Premium dark-mode design system
│   │   └── js/charts.js           # Chart.js utilities
│   └── templates/
│       ├── base.html              # Master layout
│       ├── dashboard.html         # Executive overview
│       ├── revenue.html           # Revenue analytics
│       ├── products.html          # Product analytics
│       ├── customers.html         # Customer analytics
│       └── ask_data.html          # GenAI NL query interface
│
├── sql/
│   └── verification_queries.sql  # Business intelligence validation queries
│
└── docs/
    ├── INSTALLATION.md
    ├── SNOWFLAKE_SETUP.md
    ├── DBT_SETUP.md
    ├── GEMINI_SETUP.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

---

## ⚡ Quick Start

### 1. Install Python Dependencies

```bash
cd flask_app
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Snowflake and Gemini credentials
```

### 3. Generate Data

```bash
python etl/generate_data.py
python scraper/scraper.py
```

### 4. Set Up Snowflake

Run `etl/snowflake_setup.sql` in your Snowflake worksheet, then:

```bash
python etl/load_to_snowflake.py
```

### 5. Run dbt Transformations

```bash
cd dbt_project
dbt deps
dbt run
dbt test
```

### 6. Launch Dashboard

```bash
cd flask_app
python app.py
# Open http://localhost:5000
```

---

## 🛠️ Tech Stack

| Layer              | Technology                        |
|--------------------|-----------------------------------|
| Data Generation    | Python, Faker, Pandas, NumPy      |
| Web Scraping       | BeautifulSoup4                    |
| Cloud Warehouse    | Snowflake (X-Small)               |
| ETL Loading        | snowflake-connector-python        |
| Transformations    | dbt-core + dbt-snowflake          |
| Web Framework      | Flask 3.0                         |
| Frontend           | Bootstrap 5, Chart.js, Vanilla JS |
| GenAI              | Google Gemini 1.5 Flash           |
| Fonts              | Google Fonts (Inter, JetBrains Mono) |

---

## 📊 Data Model

```
fct_sales ←→ dim_customer
     ↕            ↕
dim_product   dim_date
```

### Fact Table: `fct_sales`
- Grain: one row per order line item
- Metrics: revenue, cogs, gross_margin, discount_amount, competitor_price_delta

### Dimensions
- **dim_customer**: Customer profiles + RFM attributes
- **dim_product**: Product catalog + competitor enrichment
- **dim_date**: Full date spine 2023–2026

---

## 🤖 GenAI Interface

The "Ask Your Data" feature uses Google Gemini to:

1. Accept plain-English business questions
2. Generate safe, validated Snowflake SQL
3. Apply SQL guardrails (no DML/DDL, injection protection)
4. Execute queries and format results
5. Display with CSV export

**Example queries:**
- "Show total revenue for top 5 customers"
- "Which product categories have the highest margins?"
- "Compare our prices with competitors"
- "Show monthly revenue trends for 2024"
- "List our most overpriced products"

---

## 📝 License

University capstone project — for educational purposes.
