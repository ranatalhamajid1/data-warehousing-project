# Gemini API Setup Guide

## 1. Get a Gemini API Key

1. Go to **https://aistudio.google.com/**
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API Key"**
4. Copy the key (starts with `AIza...`)

**Free tier limits:**
- 15 requests/minute (RPM)
- 1 million tokens/minute
- 1,500 requests/day
- No credit card required

---

## 2. Configure the Key

In `flask_app/.env`:
```env
GEMINI_API_KEY=AIzaSyYour-Key-Here
GEMINI_MODEL=gemini-1.5-flash
```

Supported models:
| Model | Speed | Best For |
|-------|-------|----------|
| `gemini-1.5-flash` | Fast | Default — SQL generation |
| `gemini-1.5-pro` | Slower, smarter | Complex multi-table queries |

---

## 3. Test the Integration

```python
# Quick test script
import os
import google.generativeai as genai

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say 'Gemini is ready!'")
print(response.text)
```

---

## 4. SQL Generation Flow

```
User Question
    │
    ▼
gemini_sql_agent.py
    │  ├─ Inject SCHEMA_CONTEXT (table definitions)
    │  ├─ Prompt: "Convert to Snowflake SQL"
    │  └─ Temperature: 0.1 (deterministic)
    │
    ▼
Gemini API Response (JSON: {sql, explanation})
    │
    ▼
SQL Validation
    │  ├─ Must start with SELECT
    │  ├─ No DML/DDL keywords
    │  ├─ No injection patterns
    │  └─ Must reference RETAIL_DW tables
    │
    ▼
Execute on Snowflake (or rule-based fallback)
    │
    ▼
Display Results
```

---

## 5. Prompt Engineering Details

The agent injects complete schema context including:
- All table names with fully-qualified paths
- All column names and data types
- Business rules (date math, Snowflake syntax)
- Hard constraints (SELECT only, 1000 row LIMIT)

---

## 6. SQL Guardrails

The following are blocked regardless of what Gemini generates:

```python
BLOCKED_KEYWORDS = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
    'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC',
    'EXECUTE', 'CALL', 'MERGE'
]

INJECTION_PATTERNS = [
    '--',                        # SQL comments
    '/* ... */',                 # Block comments  
    'UNION SELECT ... password', # Data exfiltration
    'INFORMATION_SCHEMA',        # Schema introspection
    'xp_cmdshell',               # Command execution
]
```

---

## 7. Demo Mode (No API Key)

If `GEMINI_API_KEY` is not set, the agent uses **rule-based SQL generation**:

| Question Keywords | Generated Query |
|-------------------|-----------------|
| "top customers"   | Pre-built TOP_CUSTOMERS query |
| "monthly revenue" | Monthly aggregation from DAILY_REVENUE |
| "margin/profit"   | MOST_PROFITABLE_PRODUCTS query |
| "competitor/price"| COMPETITOR_PRICING_INDEX query |
| "segment/RFM"     | CUSTOMER_LTV segmentation query |
| anything else     | Overall FCT_SALES summary |
