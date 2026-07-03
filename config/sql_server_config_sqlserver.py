
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def get_sql_server_connection():
    """
    Tạo kết nối đến SQL Server Database FortressVault_Core
    """
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "FortressVault_Core")
    username = os.getenv("SQL_USERNAME", "sa")
    password = os.getenv("SQL_PASSWORD", "")
    driver = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

    connection_string = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)

