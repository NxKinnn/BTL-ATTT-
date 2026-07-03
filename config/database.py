
import os
import pyodbc
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()


def get_connection_string() -> str:
    server = os.getenv("SQL_SERVER", "localhost")
    database = os.getenv("SQL_DATABASE", "FortressVault_Core")
    username = os.getenv("SQL_USERNAME", None)
    password = os.getenv("SQL_PASSWORD", None)
    driver = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

    if username and password:
        # SQL Server Authentication
        return (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )
    else:
        # Windows Authentication
        return (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )


def get_connection() -> pyodbc.Connection:
    conn_str = get_connection_string()
    return pyodbc.connect(conn_str)


def row_to_dict(cursor: pyodbc.Cursor, row: pyodbc.Row) -> Dict[str, Any]:
    return dict(zip([column[0] for column in cursor.description], row))


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'roles')
        CREATE TABLE roles (
            role_id INT IDENTITY(1,1) PRIMARY KEY,
            role_name NVARCHAR(50) NOT NULL UNIQUE,
            description NVARCHAR(255)
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
        CREATE TABLE users (
            user_id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(100) NOT NULL UNIQUE,
            password_hash VARBINARY(255) NOT NULL,
            role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
            is_active BIT DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'user_security_profiles')
        CREATE TABLE user_security_profiles (
            profile_id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id) UNIQUE,
            salt VARBINARY(255) NOT NULL,
            encrypted_private_key NVARCHAR(MAX) NOT NULL,
            public_key NVARCHAR(MAX) NOT NULL,
            key_derivation_iterations INT NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'categories')
        CREATE TABLE categories (
            category_id INT IDENTITY(1,1) PRIMARY KEY,
            category_name NVARCHAR(100) NOT NULL UNIQUE,
            description NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'cipher_configs')
        CREATE TABLE cipher_configs (
            cipher_config_id INT IDENTITY(1,1) PRIMARY KEY,
            algorithm_name NVARCHAR(50) NOT NULL,
            key_size INT NOT NULL,
            mode NVARCHAR(50) NOT NULL,
            description NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'vault_credentials')
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
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'log_actions')
        CREATE TABLE log_actions (
            action_id INT PRIMARY KEY,
            action_name NVARCHAR(100) NOT NULL UNIQUE,
            description NVARCHAR(255)
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_logs')
        CREATE TABLE audit_logs (
            audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            action_id INT NOT NULL FOREIGN KEY REFERENCES log_actions(action_id),
            user_id INT NULL FOREIGN KEY REFERENCES users(user_id),
            ip_address NVARCHAR(50),
            user_agent NVARCHAR(255),
            action_details NVARCHAR(MAX),
            created_at DATETIME DEFAULT GETDATE()
        )
    """)

    # Insert default data
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM roles)
        BEGIN
            INSERT INTO roles (role_name, description) VALUES
            (N'User', N'Regular user managing their own vault'),
            (N'Admin', N'System administrator'),
            (N'Auditor', N'User who can only view audit logs')
        END
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM categories)
        BEGIN
            INSERT INTO categories (category_name, description) VALUES
            (N'Email', N'Email account credentials'),
            (N'Social Media', N'Social media credentials'),
            (N'Finance', N'Financial and banking credentials'),
            (N'Other', N'Other types of credentials')
        END
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM cipher_configs)
        BEGIN
            INSERT INTO cipher_configs (algorithm_name, key_size, mode, description) VALUES
            (N'AES-GCM', 256, N'GCM', N'Advanced Encryption Standard 256-bit in Galois/Counter Mode'),
            (N'TripleDES', 168, N'CBC', N'Triple Data Encryption Standard (legacy mode)')
        END
    """)

    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM log_actions)
        BEGIN
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
        END
    """)

    conn.commit()
    conn.close()

