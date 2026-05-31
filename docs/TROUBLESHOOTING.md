# Troubleshooting Guide

## Data Generation Issues

### `ModuleNotFoundError: No module named 'faker'`
```bash
pip install faker pandas numpy
```

### CSV files not created
```bash
# Check the data/ directory was created
python etl/generate_data.py
ls data/
```

---

## Snowflake Issues

### `snowflake.connector.errors.DatabaseError: 250001`
**Cause**: Invalid account identifier
**Fix**: Use the format `accountname.regionid` (e.g., `abc12345.us-east-1`)

### `250006: User is temporarily locked out`
**Cause**: Too many failed login attempts
**Fix**: Reset password in Snowflake UI → Admin → Users

### `002003: SQL compilation error: Object 'RETAIL_DW.RAW.STG_CUSTOMERS' does not exist`
**Cause**: `snowflake_setup.sql` was not run
**Fix**: Run the setup SQL script first, then retry the loader

### Row count mismatch after loading
**Cause**: Duplicate primary keys in CSV
**Fix**:
```python
# In generate_data.py, verify:
assert customers_df['customer_id'].is_unique
assert products_df['product_id'].is_unique
```

---

## dbt Issues

### `dbt.exceptions.DbtProfileError: Could not find profile named 'retail_analytics'`
**Fix**: Ensure `profiles.yml` is in the `dbt_project/` directory:
```bash
ls dbt_project/profiles.yml
```

### `dbt.exceptions.Runtime: Could not find package 'dbt_utils'`
**Fix**:
```bash
cd dbt_project
dbt deps
```

### Test failures: `relationships` test
**Cause**: FK orphans in data
**Fix**: Rerun `generate_data.py` with the fixed seed — the generator includes FK validation

### `Object 'RETAIL_DW.STAGING.STG_CUSTOMERS' does not exist`
**Cause**: dbt schemas not matching Snowflake
**Fix**: Check `generate_schema_name.sql` macro; ensure SYSADMIN role can create schemas

---

## Flask App Issues

### App starts but shows only mock data
**Cause**: `.env` not configured or missing
**Fix**:
```bash
# Check .env exists
ls flask_app/.env

# Check variables are loaded
python -c "from dotenv import load_dotenv; load_dotenv('flask_app/.env'); import os; print(os.environ.get('SNOWFLAKE_ACCOUNT','NOT SET'))"
```

### `Address already in use` on port 5000
**Fix**:
```bash
# Kill process on port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in .env:
PORT=5001
```

### Gemini API errors: `429 Resource Exhausted`
**Cause**: Free tier rate limit (15 RPM)
**Fix**: Wait 60 seconds; or upgrade to paid tier; or use demo mode (remove API key)

### Ask Your Data returns `SQL safety check failed`
**Cause**: Gemini generated a non-SELECT statement
**Fix**: Rephrase question as a data retrieval question, not a command

---

## Chart.js Issues

### Charts not rendering
**Fix**: Check browser console for errors. Ensure Chart.js CDN loaded:
```html
<!-- Verify this is in base.html -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
```

---

## Performance Tips

- Snowflake queries > 30s: Increase warehouse size to SMALL temporarily
- Large CSV loads: Increase `chunk_size` in `load_to_snowflake.py` to 10,000
- dbt slow: Increase `threads` in `profiles.yml` to 8
