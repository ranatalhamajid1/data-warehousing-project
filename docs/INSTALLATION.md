# Installation Guide

## Prerequisites

| Requirement     | Version   | Notes                           |
|-----------------|-----------|---------------------------------|
| Python          | 3.10+     | 3.11 or 3.12 recommended       |
| pip             | 23+       | Bundled with Python             |
| Git             | Any       | Optional                        |
| Snowflake Trial | Free      | 30-day free trial available     |
| Gemini API Key  | Free tier | 15 RPM free on Gemini 1.5 Flash |

---

## Step 1: Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r flask_app/requirements.txt
```

### Verify installation
```bash
python -c "import pandas, faker, bs4, flask, snowflake.connector; print('All packages OK')"
```

---

## Step 2: Environment Variables

```bash
# Copy the example file
copy flask_app\.env.example flask_app\.env

# Edit with your credentials
notepad flask_app\.env
```

Fill in all values:
```env
SNOWFLAKE_ACCOUNT=your-account-identifier
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
GEMINI_API_KEY=your-gemini-key
FLASK_SECRET_KEY=some-random-string-32chars
```

---

## Step 3: Generate Data

```bash
# Generate all synthetic datasets
python etl/generate_data.py

# Scrape competitor prices
python scraper/scraper.py
```

Expected output in `data/`:
- customers.csv — 10,000 rows
- products.csv — 500 rows
- orders.csv — 50,000 rows
- order_items.csv — 150,000 rows
- competitor_prices.csv — ~40+ rows

---

## Step 4: Snowflake Setup

See [SNOWFLAKE_SETUP.md](SNOWFLAKE_SETUP.md) for detailed steps.

```bash
# After running snowflake_setup.sql, load data:
python etl/load_to_snowflake.py
```

---

## Step 5: dbt Setup

See [DBT_SETUP.md](DBT_SETUP.md) for detailed steps.

```bash
cd dbt_project
pip install dbt-snowflake
dbt deps
dbt run
dbt test
```

---

## Step 6: Run Flask App

```bash
cd flask_app
python app.py
```

Open: http://localhost:5000

> **Demo Mode**: If Snowflake credentials are not set, the app runs with realistic mock data — all pages and charts work without any cloud account.

---

## Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: faker` | Run `pip install -r requirements.txt` |
| `ImportError: snowflake.connector` | Run `pip install snowflake-connector-python[pandas]` |
| Flask port 5000 in use | Set `PORT=5001` in `.env` |
| Snowflake timeout | Check VPN/firewall; verify account identifier |
