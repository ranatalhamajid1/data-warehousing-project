"""
Enterprise Retail Analytics Engine
dbt Run Automation
Loads environment variables from flask_app/.env and executes dbt deps and dbt run
"""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from flask_app/.env
load_dotenv(Path(__file__).parent.parent / "flask_app" / ".env")

def run_cmd(args, cwd) -> bool:
    print(f"Running: {' '.join(args)} in {cwd}...")
    env = os.environ.copy()
    # Force colors in output
    env["DBT_COLOR"] = "True"
    res = subprocess.run(args, cwd=cwd, env=env, shell=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with exit code: {res.returncode}")
        return False
    return True

def main():
    dbt_dir = Path(__file__).parent.parent / "dbt_project"
    
    # 1. Install dependencies (dbt_utils)
    print("\nInstalling dbt packages...")
    if not run_cmd(["dbt", "deps", "--profiles-dir", "."], dbt_dir):
        return
        
    # 2. Execute models
    print("\nExecuting dbt transformations on Snowflake...")
    if not run_cmd(["dbt", "run", "--profiles-dir", "."], dbt_dir):
        return
        
    print("\n[SUCCESS] dbt models built and executed successfully in Snowflake!")

if __name__ == "__main__":
    main()
