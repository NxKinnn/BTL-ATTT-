
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# Get DB config
SQL_SERVER = os.getenv("SQL_SERVER", "DESKTOP-35BPOEM\\SQLEXPRESS")
SQL_DATABASE = os.getenv("SQL_DATABASE", "FortressVault_Core")
SQL_USERNAME = os.getenv("SQL_USERNAME", "sa")
SQL_PASSWORD = os.getenv("SQL_PASSWORD", "12345678")
SQL_DRIVER = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

print(f"Connecting to SQL Server: {SQL_SERVER}...")

try:
    # First connect to master to check if database exists
    master_conn_str = f"DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};UID={SQL_USERNAME};PWD={SQL_PASSWORD};TrustServerCertificate=yes;"
    master_conn = pyodbc.connect(master_conn_str)
    master_conn.autocommit = True
    master_cursor = master_conn.cursor()
    
    # Check if database exists
    master_cursor.execute("SELECT name FROM sys.databases WHERE name = ?", (SQL_DATABASE,))
    db_exists = master_cursor.fetchone()
    
    if not db_exists:
        print(f"Database {SQL_DATABASE} does NOT exist! Please run setup_database.sql first!")
        exit(1)
    
    print(f"Database {SQL_DATABASE} exists!")
    
    # Now connect to the database
    conn_str = f"DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD};TrustServerCertificate=yes;"
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Check tables
    required_tables = ['roles', 'users', 'user_security_profiles', 'categories', 
                      'cipher_configs', 'vault_credentials', 'log_actions', 'audit_logs']
    
    print("\nChecking tables:")
    for table in required_tables:
        cursor.execute("SELECT name FROM sys.tables WHERE name = ?", (table,))
        exists = cursor.fetchone()
        status = "[OK] EXISTS" if exists else "[ERROR] MISSING"
        print(f"  {table}: {status}")
    
    # Check initial data
    print("\nChecking initial data:")
    cursor.execute("SELECT COUNT(*) FROM roles")
    print(f"  Roles: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    print(f"  Categories: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM cipher_configs")
    print(f"  Cipher Configs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM log_actions")
    print(f"  Log Actions: {cursor.fetchone()[0]}")
    
    print("\n[OK] Database check complete!")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

