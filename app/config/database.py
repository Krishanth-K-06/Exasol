import ssl
import logging
from typing import Generator, Any, Dict, List, Optional
import pyexasol
from app.config.settings import settings

logger = logging.getLogger(__name__)


def create_exasol_connection() -> pyexasol.ExaConnection:
    """
    Creates and returns a new pyexasol connection using app settings.
    Handles SSL options for local self-signed certificates.
    """
    websocket_sslopt: Dict[str, Any] = {}
    if not settings.EXASOL_VALIDATE_CERT:
        # Exasol Personal uses a local self-signed certificate by default
        websocket_sslopt["cert_reqs"] = ssl.CERT_NONE

    connection_params: Dict[str, Any] = {
        "dsn": settings.EXASOL_DSN,
        "user": settings.EXASOL_USER,
        "password": settings.EXASOL_PASSWORD,
        "encryption": settings.EXASOL_ENCRYPTION,
        "connection_timeout": settings.EXASOL_CONNECTION_TIMEOUT,
        "socket_timeout": settings.EXASOL_SOCKET_TIMEOUT,
        "websocket_sslopt": websocket_sslopt,
    }

    if settings.EXASOL_SCHEMA:
        connection_params["schema"] = settings.EXASOL_SCHEMA

    return pyexasol.connect(**connection_params)


def get_db() -> Generator[pyexasol.ExaConnection, None, None]:
    """
    FastAPI dependency that yields an active Exasol database connection
    and guarantees proper closure when the request completes.
    """
    connection = create_exasol_connection()
    try:
        yield connection
    finally:
        try:
            connection.close()
        except Exception as e:
            logger.warning(f"Error closing Exasol connection: {e}")


def check_db_connection() -> bool:
    """
    Utility to verify database connectivity on application startup or health checks.
    """
    try:
        connection = create_exasol_connection()
        val = connection.execute("SELECT 1 AS TEST").fetchval()
        connection.close()
        if val == 1:
            logger.info("Successfully connected to Exasol database.")
            return True
        return False
    except Exception as e:
        logger.error(f"Exasol connection failed: {e}")
        return False


def execute_query(query: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Helper function to run a query and fetch all results as a list of dictionaries.
    """
    connection = create_exasol_connection()
    try:
        statement = connection.execute(query, query_params or {})
        columns = list(statement.columns().keys())
        rows = statement.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        connection.close()
