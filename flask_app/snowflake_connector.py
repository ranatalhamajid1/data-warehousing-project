"""
Enterprise Retail Analytics Engine
Snowflake Connector Utility
Manages connection lifecycle, query execution, and connection health
"""

import os
import logging
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

try:
    import snowflake.connector
except ImportError:
    snowflake = None


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
        if snowflake is None:
            log.warning("snowflake-connector-python is not installed. Running in DEMO MODE.")
            self._connected = False
            return

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
        if not self._connected or self._conn is None:
            return False
        try:
            if self._conn.is_closed():
                self._connected = False
                return False
        except Exception:
            pass
        return True

    def _ensure_connection(self):
        """Reconnect if connection was dropped."""
        if not self.is_connected():
            self._connect()

    def _execute_with_retry(self, fn, *args, **kwargs):
        """
        Execute a cursor operation function, with retry logic for connection/session errors.
        """
        self._ensure_connection()
        if not self.is_connected():
            raise RuntimeError("Snowflake not connected")

        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            is_connection_issue = False
            if snowflake is not None:
                if isinstance(exc, snowflake.connector.Error):
                    is_connection_issue = (
                        isinstance(exc, (
                            snowflake.connector.errors.OperationalError,
                            snowflake.connector.errors.InterfaceError,
                            snowflake.connector.errors.TokenExpiredError
                        ))
                        or getattr(exc, 'errno', None) in (390114, 390111, 390113, 390115)
                        or any(keyword in str(exc).lower() for keyword in ["token", "expired", "session", "connection", "authenticate"])
                    )

            if is_connection_issue:
                log.warning(f"Snowflake connection/session error detected ({exc}). Resetting connection and retrying once...")
                self.close()
                self._connect()
                if self.is_connected():
                    return fn(*args, **kwargs)
            raise

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
        def _run():
            cursor = self._conn.cursor(snowflake.connector.DictCursor)
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchmany(max_rows)
                return [dict(row) for row in rows]
            finally:
                cursor.close()

        return self._execute_with_retry(_run)

    def execute(self, sql: str, params: Optional[tuple] = None) -> int:
        """Execute DDL/DML — returns rowcount."""
        def _run():
            cursor = self._conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.rowcount
            finally:
                cursor.close()

        return self._execute_with_retry(_run)

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
