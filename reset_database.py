
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

print("=== Resetting database ===")

# Connect to master database first
master_conn_str = f"DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};UID={SQL_USERNAME};PWD={SQL_PASSWORD};TrustServerCertificate=yes;"
master_conn = pyodbc.connect(master_conn_str)
master_conn.autocommit = True
master_cursor = master_conn.cursor()

# Drop existing database if exists
print("1. Dropping existing database...")
try:
    master_cursor.execute(f"ALTER DATABASE [{SQL_DATABASE}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;")
    master_cursor.execute(f"DROP DATABASE [{SQL_DATABASE}];")
    print(f"   Dropped database {SQL_DATABASE}")
except Exception as e:
    print(f"   Note: {str(e)}")

# Create new database
print("2. Creating new database...")
master_cursor.execute(f"CREATE DATABASE [{SQL_DATABASE}];")
print(f"   Created database {SQL_DATABASE}")

master_conn.close()

# Now connect to the new database
conn_str = f"DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD};TrustServerCertificate=yes;"
conn = pyodbc.connect(conn_str)
conn.autocommit = False
cursor = conn.cursor()

try:
    print("\n3. Creating tables...")
    # Create all tables
    cursor.execute("""
        CREATE TABLE roles (
            role_id INT IDENTITY(1,1) PRIMARY KEY,
            role_name NVARCHAR(50) NOT NULL UNIQUE,
            description NVARCHAR(255)
        );
    """)
    
    cursor.execute("""
        CREATE TABLE users (
            user_id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(100) NOT NULL UNIQUE,
            password_hash VARBINARY(255) NOT NULL,
            role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
            is_active BIT DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    cursor.execute("""
        CREATE TABLE user_security_profiles (
            profile_id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id) UNIQUE,
            salt VARBINARY(255) NOT NULL,
            encrypted_private_key NVARCHAR(MAX) NOT NULL,
            public_key NVARCHAR(MAX) NOT NULL,
            key_derivation_iterations INT NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    cursor.execute("""
        CREATE TABLE categories (
            category_id INT IDENTITY(1,1) PRIMARY KEY,
            category_name NVARCHAR(100) NOT NULL UNIQUE,
            description NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    cursor.execute("""
        CREATE TABLE cipher_configs (
            cipher_config_id INT IDENTITY(1,1) PRIMARY KEY,
            algorithm_name NVARCHAR(50) NOT NULL,
            key_size INT NOT NULL,
            mode NVARCHAR(50) NOT NULL,
            description NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    cursor.execute("""
        CREATE TABLE vault_credentials (
            vault_id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
            category_id INT NULL FOREIGN KEY REFERENCES categories(category_id),
            item_name NVARCHAR(255) NOT NULL,
            encrypted_username NVARCHAR(MAX),
            encrypted_password NVARCHAR(MAX) NOT NULL,
            encrypted_notes NVARCHAR(MAX),
            iv NVARCHAR(255) NOT NULL,
            auth_tag NVARCHAR(255) NOT NULL,
            cipher_config_id INT NOT NULL FOREIGN KEY REFERENCES cipher_configs(cipher_config_id),
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    cursor.execute("""
        CREATE TABLE log_actions (
            action_id INT PRIMARY KEY,
            action_name NVARCHAR(100) NOT NULL UNIQUE,
            description NVARCHAR(255)
        );
    """)
    
    cursor.execute("""
        CREATE TABLE audit_logs (
            audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            action_id INT NOT NULL FOREIGN KEY REFERENCES log_actions(action_id),
            user_id INT NULL FOREIGN KEY REFERENCES users(user_id),
            ip_address NVARCHAR(50),
            user_agent NVARCHAR(255),
            action_details NVARCHAR(MAX),
            created_at DATETIME DEFAULT GETDATE()
        );
    """)
    
    print("   Created all tables successfully!")
    
    print("\n4. Inserting initial data...")
    
    # Insert roles
    cursor.execute("""
        INSERT INTO roles (role_name, description) VALUES
        (N'User', N'Regular user managing their own vault'),
        (N'Admin', N'System administrator'),
        (N'Auditor', N'User who can only view audit logs');
    """)
    print("   Inserted roles")
    
    # Insert categories
    cursor.execute("""
        INSERT INTO categories (category_name, description) VALUES
        (N'Email', N'Email account credentials'),
        (N'Social Media', N'Social media credentials'),
        (N'Finance', N'Financial and banking credentials'),
        (N'Other', N'Other types of credentials');
    """)
    print("   Inserted categories")
    
    # Insert cipher configs
    cursor.execute("""
        INSERT INTO cipher_configs (algorithm_name, key_size, mode, description) VALUES
        (N'AES-GCM', 256, N'GCM', N'Advanced Encryption Standard 256-bit in Galois/Counter Mode'),
        (N'TripleDES', 168, N'CBC', N'Triple Data Encryption Standard (legacy mode)'),
        (N'AES-CBC', 256, N'CBC', N'Advanced Encryption Standard 256-bit in Cipher Block Chaining mode');
    """)
    print("   Inserted cipher configs")
    
    # Insert log actions
    cursor.execute("""
        INSERT INTO log_actions (action_id, action_name, description) VALUES
        (1, N'REGISTER', N'User registered a new account'),
        (2, N'LOGIN_SUCCESS', N'User logged in successfully'),
        (3, N'LOGIN_FAILED', N'User failed to log in'),
        (4, N'VAULT_ADD', N'User added a new vault item'),
        (5, N'VAULT_VIEW', N'User viewed/decrypted a vault item'),
        (6, N'VAULT_UPDATE', N'User updated a vault item'),
        (7, N'VAULT_DELETE', N'User deleted a vault item'),
        (8, N'AUDIT_VIEW', N'Auditor viewed audit logs'),
        (9, N'LOGOUT', N'User logged out');
    """)
    print("   Inserted log actions")
    
    conn.commit()
    print("\n=== Database reset complete! ===")
    
except Exception as e:
    conn.rollback()
    print(f"\n[ERROR] Failed to reset database: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
