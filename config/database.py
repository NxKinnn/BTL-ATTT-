
"""
Database Configuration and Connection Pool for SQL Server (pyodbc)
FortressVault - Secure Personal Data Vault
"""
import os
import pyodbc
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

load_dotenv()

# Configuration
SQL_SERVER = os.getenv("SQL_SERVER", "DESKTOP-35BPOEM\\SQLEXPRESS")
SQL_DATABASE = os.getenv("SQL_DATABASE", "FortressVault_Core")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "12345678")
SQL_DRIVER = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

def get_connection_string() -> str:
    """
    Get SQL Server connection string with SQL Server Authentication
    """
    return (
        f"DRIVER={SQL_DRIVER};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};"
        f"PWD={SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )

# Connection pool management
_connection_pool = []
MAX_POOL_SIZE = 10

def get_connection() -> pyodbc.Connection:
    """
    Get a database connection from pool or create new
    """
    if _connection_pool:
        conn = _connection_pool.pop()
        try:
            conn.execute("SELECT 1")
            return conn
        except pyodbc.Error:
            conn.close()
            return pyodbc.connect(get_connection_string())
    return pyodbc.connect(get_connection_string())

def close_connection(conn: pyodbc.Connection) -> None:
    """
    Return connection to pool or close
    """
    try:
        if len(_connection_pool) < MAX_POOL_SIZE:
            _connection_pool.append(conn)
        else:
            conn.close()
    except Exception:
        pass

def row_to_dict(cursor: pyodbc.Cursor, row: pyodbc.Row) -> Dict[str, Any]:
    """
    Convert a pyodbc row to dictionary
    """
    return {column[0]: row[i] for i, column in enumerate(cursor.description)}

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as list of dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return [row_to_dict(cursor, row) for row in rows]
    finally:
        cursor.close()
        close_connection(conn)

def execute_non_query(query: str, params: Optional[tuple] = None, return_id: bool = False) -> Optional[int]:
    """
    Execute an INSERT, UPDATE, DELETE query
    If return_id=True, returns last inserted ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    last_id = None
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        if return_id:
            cursor.execute("SELECT @@IDENTITY")
            last_id = cursor.fetchone()[0]
        return last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        close_connection(conn)

@contextmanager
def transaction():
    """
    Context manager for database transactions
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        close_connection(conn)

