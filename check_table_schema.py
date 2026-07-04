
from config.database import get_connection

def check_table_schema(table_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get column info
    cursor.execute(f"""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.is_nullable,
            c.is_identity
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        WHERE c.object_id = OBJECT_ID(?)
        ORDER BY c.column_id
    """, (table_name,))
    
    print(f"\n=== Schema for table: {table_name} ===")
    for row in cursor.fetchall():
        print(f"  {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, identity: {row.is_identity})")
    
    cursor.close()
    conn.close()

# Check all tables
tables_to_check = ['categories', 'roles', 'users', 'user_security_profiles', 'cipher_configs', 'vault_credentials', 'log_actions', 'audit_logs']
for table in tables_to_check:
    check_table_schema(table)
