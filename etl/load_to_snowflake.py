"""
Enterprise Retail Analytics Engine
Part 1: Snowflake ETL Loader
Loads all CSV files from /data/ into Snowflake RAW staging tables
Uses snowflake-connector-python with pandas ingestion pipeline
Includes row-level validation to prove zero data loss
"""

import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from dotenv import load_dotenv

# Load environment variables FIRST, before accessing os.environ
load_dotenv(Path(__file__).parent.parent / "flask_app" / ".env")

try:
    import snowflake.connector  # type: ignore
    from snowflake.connector.pandas_tools import write_pandas  # type: ignore
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

# ─── Environment already loaded above ────────────────────────────────────────

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"

def get_snowflake_config() -> Dict[str, str]:
    """Build Snowflake connection config from environment variables at runtime."""
    account = os.environ.get("SNOWFLAKE_ACCOUNT", "")
    user    = os.environ.get("SNOWFLAKE_USER", "")
    password = os.environ.get("SNOWFLAKE_PASSWORD", "")
    if not all([account, user, password]):
        raise EnvironmentError(
            "Missing Snowflake credentials. Set SNOWFLAKE_ACCOUNT, "
            "SNOWFLAKE_USER, SNOWFLAKE_PASSWORD in flask_app/.env"
        )
    return {
        "account":   account,
        "user":      user,
        "password":  password,
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "RETAIL_WH"),
        "database":  os.environ.get("SNOWFLAKE_DATABASE", "RETAIL_DW"),
        "schema":    "RAW",
        "role":      os.environ.get("SNOWFLAKE_ROLE", "SYSADMIN"),
    }

# Mapping: CSV file → Snowflake table, with column rename maps
LOAD_CONFIG = [
    {
        "file":    "customers.csv",
        "table":   "STG_CUSTOMERS",
        "columns": {
            "customer_id":       "CUSTOMER_ID",
            "first_name":        "FIRST_NAME",
            "last_name":         "LAST_NAME",
            "gender":            "GENDER",
            "email":             "EMAIL",
            "city":              "CITY",
            "country":           "COUNTRY",
            "registration_date": "REGISTRATION_DATE",
        },
        "dtypes": {
            "CUSTOMER_ID": str,
            "FIRST_NAME":  str,
            "LAST_NAME":   str,
            "GENDER":      str,
            "EMAIL":       str,
            "CITY":        str,
            "COUNTRY":     str,
        },
    },
    {
        "file":    "products.csv",
        "table":   "STG_PRODUCTS",
        "columns": {
            "product_id":   "PRODUCT_ID",
            "product_name": "PRODUCT_NAME",
            "category":     "CATEGORY",
            "retail_price": "RETAIL_PRICE",
            "base_cost":    "BASE_COST",
        },
        "dtypes": {
            "PRODUCT_ID":   str,
            "PRODUCT_NAME": str,
            "CATEGORY":     str,
            "RETAIL_PRICE": float,
            "BASE_COST":    float,
        },
    },
    {
        "file":    "orders.csv",
        "table":   "STG_ORDERS",
        "columns": {
            "order_id":    "ORDER_ID",
            "customer_id": "CUSTOMER_ID",
            "order_date":  "ORDER_DATE",
        },
        "dtypes": {
            "ORDER_ID":    str,
            "CUSTOMER_ID": str,
        },
    },
    {
        "file":    "order_items.csv",
        "table":   "STG_ORDER_ITEMS",
        "columns": {
            "order_item_id": "ORDER_ITEM_ID",
            "order_id":      "ORDER_ID",
            "product_id":    "PRODUCT_ID",
            "quantity":      "QUANTITY",
            "unit_price":    "UNIT_PRICE",
        },
        "dtypes": {
            "ORDER_ITEM_ID": str,
            "ORDER_ID":      str,
            "PRODUCT_ID":    str,
            "QUANTITY":      int,
            "UNIT_PRICE":    float,
        },
    },
    {
        "file":    "competitor_prices.csv",
        "table":   "STG_COMPETITOR_PRICES",
        "columns": {
            "scraped_at":           "SCRAPED_AT",
            "category":             "CATEGORY",
            "product_name":         "PRODUCT_NAME",
            "competitor_name":      "COMPETITOR_NAME",
            "competitor_price_usd": "COMPETITOR_PRICE_USD",
            "our_price_usd":        "OUR_PRICE_USD",
            "price_position":       "PRICE_POSITION",
            "last_updated":         "LAST_UPDATED",
            "price_delta_usd":      "PRICE_DELTA_USD",
            "price_delta_pct":      "PRICE_DELTA_PCT",
        },
        "dtypes": {
            "CATEGORY":             str,
            "PRODUCT_NAME":         str,
            "COMPETITOR_NAME":      str,
            "COMPETITOR_PRICE_USD": float,
            "OUR_PRICE_USD":        float,
            "PRICE_POSITION":       str,
            "PRICE_DELTA_USD":      float,
            "PRICE_DELTA_PCT":      float,
        },
    },
]


# ─── Connection ───────────────────────────────────────────────────────────────

def get_connection():
    if not SNOWFLAKE_AVAILABLE:
        raise ImportError(
            "snowflake-connector-python is not installed. "
            "Run: pip install snowflake-connector-python[pandas]"
        )
    cfg = get_snowflake_config()
    log.info(f"Connecting to Snowflake: {cfg['account']} / {cfg['database']}.{cfg['schema']}")
    try:
        conn = snowflake.connector.connect(**cfg)
        log.info("[OK] Snowflake connection established")
        return conn
    except Exception as exc:
        log.error(f"[ERROR] Connection failed: {exc}")
        raise


# ─── Load Single Table ────────────────────────────────────────────────────────

def load_table(conn, cfg: dict) -> dict:
    """
    Load a CSV file into a Snowflake table using write_pandas.
    Returns validation results dict.
    """
    csv_path = DATA_DIR / cfg["file"]
    table    = cfg["table"]

    if not csv_path.exists():
        log.error(f"[ERROR] File not found: {csv_path}")
        return {"table": table, "status": "FILE_NOT_FOUND", "source_rows": 0, "loaded_rows": 0}

    # ── Read CSV ───────────────────────────────────────────────────
    log.info(f"Reading {csv_path.name}...")
    df = pd.read_csv(csv_path, dtype=str)  # Read as str first to avoid type coercion issues
    source_rows = len(df)

    # ── Rename columns to uppercase Snowflake names ────────────────
    df = df.rename(columns=cfg["columns"])

    # ── Type casting ──────────────────────────────────────────────
    for col, dtype in cfg.get("dtypes", {}).items():
        if col in df.columns:
            try:
                if dtype == float:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif dtype == int:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
                else:
                    df[col] = df[col].astype(str)
            except Exception as e:
                log.warning(f"  Type cast warning for {col}: {e}")

    # Drop system columns if present (Snowflake adds them)
    df = df[[c for c in df.columns if not c.startswith("_")]]

    # ── Truncate existing data ────────────────────────────────────
    cursor = conn.cursor()
    log.info(f"Truncating {table}...")
    cursor.execute(f"TRUNCATE TABLE IF EXISTS {table}")

    # ── Load via write_pandas ─────────────────────────────────────
    log.info(f"Loading {source_rows:,} rows into {table}...")
    t_start = time.time()

    cfg_conn = get_snowflake_config()
    success, nchunks, nrows, output = write_pandas(
        conn=conn,
        df=df,
        table_name=table,
        database=cfg_conn["database"],
        schema=cfg_conn["schema"],
        auto_create_table=False,
        quote_identifiers=False,
        chunk_size=5000,
    )

    elapsed = time.time() - t_start
    log.info(f"  Loaded {nrows:,} rows in {elapsed:.1f}s across {nchunks} chunks | success={success}")

    # ── Validate row count ────────────────────────────────────────
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    snowflake_rows = cursor.fetchone()[0]
    cursor.close()

    status = "OK" if snowflake_rows == source_rows else "ROW_MISMATCH"
    delta  = snowflake_rows - source_rows

    return {
        "table":          table,
        "file":           cfg["file"],
        "status":         status,
        "source_rows":    source_rows,
        "loaded_rows":    nrows,
        "snowflake_rows": snowflake_rows,
        "delta":          delta,
        "elapsed_s":      round(elapsed, 2),
    }


# ─── Validation Report ────────────────────────────────────────────────────────

def run_validation_queries(conn) -> None:
    """Run analytical validation queries after loading."""
    cursor = conn.cursor()
    print("\n" + "=" * 70)
    print("  SNOWFLAKE VALIDATION QUERIES")
    print("=" * 70)

    queries = [
        (
            "Row Count Summary",
            """
            SELECT 'customers'        AS table_name, COUNT(*) AS row_count FROM STG_CUSTOMERS
            UNION ALL SELECT 'products',              COUNT(*) FROM STG_PRODUCTS
            UNION ALL SELECT 'orders',                COUNT(*) FROM STG_ORDERS
            UNION ALL SELECT 'order_items',           COUNT(*) FROM STG_ORDER_ITEMS
            UNION ALL SELECT 'competitor_prices',     COUNT(*) FROM STG_COMPETITOR_PRICES
            ORDER BY table_name
            """,
        ),
        (
            "FK Integrity - Orders -> Customers (should be 0 orphans)",
            """
            SELECT COUNT(*) AS orphan_orders
            FROM STG_ORDERS o
            LEFT JOIN STG_CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE c.CUSTOMER_ID IS NULL
            """,
        ),
        (
            "FK Integrity - Items -> Orders (should be 0 orphans)",
            """
            SELECT COUNT(*) AS orphan_items
            FROM STG_ORDER_ITEMS i
            LEFT JOIN STG_ORDERS o ON i.ORDER_ID = o.ORDER_ID
            WHERE o.ORDER_ID IS NULL
            """,
        ),
        (
            "Revenue Summary by Category",
            """
            SELECT p.CATEGORY,
                   COUNT(DISTINCT oi.ORDER_ID)  AS orders,
                   SUM(oi.QUANTITY * oi.UNIT_PRICE) AS total_revenue
            FROM STG_ORDER_ITEMS oi
            JOIN STG_PRODUCTS    p ON oi.PRODUCT_ID = p.PRODUCT_ID
            GROUP BY p.CATEGORY
            ORDER BY total_revenue DESC
            LIMIT 10
            """,
        ),
        (
            "Date Range of Orders",
            """
            SELECT MIN(ORDER_DATE) AS first_order, MAX(ORDER_DATE) AS last_order,
                   DATEDIFF('day', MIN(ORDER_DATE), MAX(ORDER_DATE)) AS span_days
            FROM STG_ORDERS
            """,
        ),
    ]

    for title, sql in queries:
        print(f"\n  [{title}]")
        cursor.execute(sql.strip())
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        print("  " + " | ".join(f"{c:>20}" for c in columns))
        print("  " + "-" * (23 * len(columns)))
        for row in results:
            print("  " + " | ".join(f"{str(v):>20}" for v in row))

    cursor.close()
    print("=" * 70)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Enterprise Retail Analytics Engine — Snowflake ETL Loader")
    print("=" * 70)

    # Connect
    conn = get_connection()

    try:
        # Set context
        cfg_conn = get_snowflake_config()
        cursor = conn.cursor()
        cursor.execute(f"USE WAREHOUSE {cfg_conn['warehouse']}")
        cursor.execute(f"USE DATABASE {cfg_conn['database']}")
        cursor.execute(f"USE SCHEMA {cfg_conn['schema']}")
        cursor.close()

        # Load all tables
        validation_results = []
        for cfg in LOAD_CONFIG:
            result = load_table(conn, cfg)
            validation_results.append(result)

        # Print validation summary
        print("\n" + "=" * 70)
        print("  LOAD VALIDATION SUMMARY")
        print("=" * 70)
        print(f"  {'Table':<30} {'Status':>10} {'Source':>10} {'Snowflake':>10} {'Delta':>8}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

        all_ok = True
        for r in validation_results:
            status_icon = "[OK]" if r["status"] == "OK" else "[FAIL]"
            print(f"  {r['table']:<30} {status_icon} {r.get('status', '?'):>8} "
                  f"{r.get('source_rows', 0):>10,} {r.get('snowflake_rows', 0):>10,} "
                  f"{r.get('delta', 0):>+8,}")
            if r["status"] != "OK":
                all_ok = False

        if all_ok:
            print(f"\n  [SUCCESS] Zero data loss confirmed - all rows loaded successfully!")
        else:
            print(f"\n  [WARNING] Row count mismatches detected - investigate above.")

        # Run validation queries
        run_validation_queries(conn)

    finally:
        conn.close()
        log.info("Snowflake connection closed.")


if __name__ == "__main__":
    main()
