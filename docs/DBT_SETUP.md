# dbt Setup Guide

## 1. Install dbt-snowflake

```bash
pip install dbt-snowflake
dbt --version
```

Expected: `dbt-core 1.7.x`, `dbt-snowflake 1.7.x`

---

## 2. Install dbt Packages

From the `dbt_project/` directory:

```bash
cd dbt_project
dbt deps
```

This installs:
- `dbt_utils` — utility macros (surrogate key, date spine)

---

## 3. Configure profiles.yml

The `profiles.yml` reads from environment variables automatically:

```bash
# Set environment variables (or use .env file)
set SNOWFLAKE_ACCOUNT=your-account
set SNOWFLAKE_USER=your-user
set SNOWFLAKE_PASSWORD=your-password
set SNOWFLAKE_WAREHOUSE=RETAIL_WH
set SNOWFLAKE_DATABASE=RETAIL_DW
set SNOWFLAKE_ROLE=SYSADMIN

# Test connection
dbt debug
```

Expected output:
```
Connection:
  account: your-account
  user: your-user
  database: RETAIL_DW
  warehouse: RETAIL_WH
  role: SYSADMIN
  schema: staging
  All checks passed!
```

---

## 4. Run Models

```bash
# Run all models in dependency order
dbt run

# Or run by layer
dbt run --select staging
dbt run --select marts
dbt run --select analytics
```

Expected run order:
1. `stg_customers`, `stg_products`, `stg_orders`, `stg_order_items`, `stg_competitor_prices`
2. `dim_customer`, `dim_product`, `dim_date`
3. `fct_sales`
4. `daily_revenue`, `top_categories`, `competitor_pricing_index`, `customer_ltv`, `top_customers`, `most_profitable_products`

---

## 5. Run Tests

```bash
dbt test
```

Tests include:
- `unique` — no duplicate keys
- `not_null` — no null primary keys
- `relationships` — FK integrity across fact and dimensions
- `accepted_values` — valid enum values

Expected: **All 40+ tests pass**

---

## 6. Generate Documentation

```bash
dbt docs generate
dbt docs serve
# Open http://localhost:8080
```

---

## Model Materialization Summary

| Schema    | Materialization | Notes                            |
|-----------|-----------------|----------------------------------|
| STAGING   | View            | Lightweight, reads from RAW      |
| MARTS     | Table           | Physical tables, clustered       |
| ANALYTICS | Table           | Pre-aggregated for dashboard     |

---

## dbt DAG (Dependency Graph)

```
RAW.STG_CUSTOMERS ──────────┐
RAW.STG_PRODUCTS ──────────┼──► dim_customer ──┐
RAW.STG_ORDERS ────────────┤    dim_product ───┼──► fct_sales ──► analytics/*
RAW.STG_ORDER_ITEMS ───────┘    dim_date ──────┘
RAW.STG_COMPETITOR_PRICES ──────────────────────► dim_product
```

---

## Adding New Models

1. Create `.sql` file in `models/<layer>/`
2. Add to `schema.yml` with description and tests
3. Run `dbt run --select <model_name>`
4. Run `dbt test --select <model_name>`
