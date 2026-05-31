# Snowflake Setup Guide

## 1. Create a Free Trial Account

1. Visit https://signup.snowflake.com/
2. Choose **Enterprise** edition (30-day free trial, no credit card)
3. Select **AWS US East (N. Virginia)** as your cloud region
4. Complete signup and verify email

---

## 2. Get Your Account Identifier

Your Snowflake account identifier appears in the URL:
```
https://<account-identifier>.snowflakecomputing.com
```

Format examples:
- `abc12345.us-east-1` (AWS)
- `xy98765.west-europe.azure` (Azure)

Set in `.env`:
```env
SNOWFLAKE_ACCOUNT=abc12345.us-east-1
```

---

## 3. Run Setup SQL

1. Log into Snowflake web UI (SnowSight)
2. Click **Worksheets** → **+ New Worksheet**
3. Open `etl/snowflake_setup.sql`
4. Copy all contents and paste into worksheet
5. Click **Run All** (or press Ctrl+Shift+Enter)

This creates:
- `RETAIL_WH` — X-Small warehouse (auto-suspend 2 min)
- `RETAIL_DW` — Database
- `RAW`, `STAGING`, `MARTS`, `ANALYTICS` schemas
- All 5 staging table DDLs
- `CSV_FORMAT` file format
- `RETAIL_STAGE` internal stage

---

## 4. Load Data via Python

```bash
# Make sure you've generated the CSV files first
python etl/generate_data.py
python scraper/scraper.py

# Load all tables
python etl/load_to_snowflake.py
```

The loader will print a validation summary:
```
  STG_CUSTOMERS     ✅ OK    10,000    10,000     +0
  STG_PRODUCTS      ✅ OK       500       500     +0
  STG_ORDERS        ✅ OK    50,000    50,000     +0
  STG_ORDER_ITEMS   ✅ OK   150,000   150,000     +0
  STG_COMPETITOR    ✅ OK        43        43     +0

  🎉 Zero data loss confirmed
```

---

## 5. Verify in Snowflake

Run this in a Snowflake worksheet:
```sql
SELECT table_name, row_count
FROM RETAIL_DW.information_schema.tables
WHERE table_schema = 'RAW'
ORDER BY row_count DESC;
```

---

## Snowflake Roles & Security

| Resource     | Value        |
|--------------|--------------|
| Role         | SYSADMIN     |
| Warehouse    | RETAIL_WH    |
| Database     | RETAIL_DW    |
| Schema (ETL) | RAW          |
| Schema (dbt) | STAGING, MARTS, ANALYTICS |

---

## Cost Management Tips

- Warehouse auto-suspends after **2 minutes** of inactivity
- X-Small = 1 credit/hour ≈ $2/hr (rarely used in this project)
- Free trial includes $400 credit
- This project uses < 5 credits total
