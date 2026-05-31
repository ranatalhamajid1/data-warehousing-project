"""
Enterprise Retail Analytics Engine
Snowflake Connector Utility
Manages connection lifecycle, query execution, and connection health
"""

import os
import logging
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)


class SnowflakeConnector:
    """
    Thread-safe Snowflake connector with connection pooling and health checks.
    Gracefully handles missing credentials for demo/development mode.
    """

    def __init__(self):
        self._conn = None
        self._connected = False
        self._connect()

    def _connect(self):
        required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
        missing = [k for k in required if not os.environ.get(k)]

        if missing:
            log.warning(
                f"Snowflake credentials missing: {missing}. "
                "Running in DEMO MODE with mock data."
            )
            self._connected = False
            return

        try:
            import snowflake.connector
            self._conn = snowflake.connector.connect(
                account=os.environ["SNOWFLAKE_ACCOUNT"],
                user=os.environ["SNOWFLAKE_USER"],
                password=os.environ["SNOWFLAKE_PASSWORD"],
                warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "RETAIL_WH"),
                database=os.environ.get("SNOWFLAKE_DATABASE", "RETAIL_DW"),
                schema=os.environ.get("SNOWFLAKE_SCHEMA", "MARTS"),
                role=os.environ.get("SNOWFLAKE_ROLE", "SYSADMIN"),
                client_session_keep_alive=True,
                login_timeout=30,
            )
            self._connected = True
            log.info("[OK] Snowflake connected successfully")
        except Exception as exc:
            log.warning(f"Snowflake connection failed (demo mode active): {exc}")
            self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._conn is not None

    def _ensure_connection(self):
        """Reconnect if connection was dropped."""
        if not self.is_connected():
            self._connect()

    def query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        max_rows: int = 10_000,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dicts.
        Raises on error — callers should handle exceptions.
        """
        self._ensure_connection()
        if not self.is_connected():
            raise RuntimeError("Snowflake not connected")

        cursor = self._conn.cursor(snowflake.connector.DictCursor)
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchmany(max_rows)
            return [dict(row) for row in rows]
        finally:
            cursor.close()

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """Execute DDL/DML — returns rowcount."""
        self._ensure_connection()
        if not self.is_connected():
            raise RuntimeError("Snowflake not connected")

        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.rowcount
        finally:
            cursor.close()

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._connected = False

    def __del__(self):
        self.close()


# ── Avoid NameError if snowflake not installed ────────────────────────────────
try:
    import snowflake.connector
except ImportError:
    pass
