"""
Enterprise Retail Analytics Engine
Snowflake Setup Executor
Connects to Snowflake and executes snowflake_setup.sql to create databases, tables, and roles
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from flask_app/.env
load_dotenv(Path(__file__).parent.parent / "flask_app" / ".env")

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

def main():
    if not SNOWFLAKE_AVAILABLE:
        print("[ERROR] snowflake-connector-python is not installed. Run: pip install snowflake-connector-python")
        return

    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    user = os.environ.get("SNOWFLAKE_USER")
    password = os.environ.get("SNOWFLAKE_PASSWORD")
    
    if not all([account, user, password]):
        print("[ERROR] Snowflake credentials missing in flask_app/.env")
        return
        
    print(f"Connecting to Snowflake account {account} as user {user}...")
    try:
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            login_timeout=30
        )
        print("[OK] Connected to Snowflake successfully!")
    except Exception as exc:
        print(f"[ERROR] Failed to connect: {exc}")
        return

    sql_file = Path(__file__).parent / "snowflake_setup.sql"
    if not sql_file.exists():
        print(f"[ERROR] SQL file not found: {sql_file}")
        conn.close()
        return
        
    print(f"Reading DDL from {sql_file.name}...")
    with open(sql_file, encoding="utf-8") as fh:
        sql_content = fh.read()
        
    # Clean single-line SQL comments and split by semicolon
    sql_clean = re.sub(r'--.*', '', sql_content)
    statements = sql_clean.split(';')
    
    cursor = conn.cursor()
    print("Executing database setup statements...")
    for idx, stmt in enumerate(statements):
        stmt_clean = stmt.strip()
        if not stmt_clean:
            continue
            
        snippet = stmt_clean.split('\n')[0][:60]
        print(f"  [{idx+1}/{len(statements)}] Executing: {snippet}...")
        try:
            cursor.execute(stmt_clean)
        except Exception as exc:
            # Grant statements or role creations might occasionally raise non-critical warnings
            # depending on whether the user is ACCOUNTADMIN or not. Let's warn instead of crash.
            if any(kwd in stmt_clean.upper() for kwd in ["GRANT", "ROLE"]):
                print(f"  [WARNING] Non-critical statement failed: {exc}")
            else:
                print(f"  [ERROR] Database setup statement failed: {exc}")
                cursor.close()
                conn.close()
                return
                
    cursor.close()
    conn.close()
    print("[SUCCESS] Snowflake Database Setup Complete!")

if __name__ == "__main__":
    main()
