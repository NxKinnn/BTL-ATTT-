
import sqlite3
import os

# Use environment variable DB_PATH, default to vault.db
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'vault.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(cursor, row):
    return dict(row)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash BLOB NOT NULL,
            role_id INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(role_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_security_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            salt BLOB NOT NULL,
            encrypted_private_key TEXT NOT NULL,
            public_key TEXT NOT NULL,
            key_derivation_iterations INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cipher_configs (
            cipher_config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm_name TEXT NOT NULL,
            key_size INTEGER NOT NULL,
            mode TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vault_credentials (
            vault_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            item_name TEXT NOT NULL,
            encrypted_username TEXT,
            encrypted_password TEXT NOT NULL,
            encrypted_notes TEXT,
            iv TEXT NOT NULL,
            auth_tag TEXT NOT NULL,
            cipher_config_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (cipher_config_id) REFERENCES cipher_configs(cipher_config_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_actions (
            action_id INTEGER PRIMARY KEY,
            action_name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id INTEGER NOT NULL,
            user_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            action_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (action_id) REFERENCES log_actions(action_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Insert default data
    cursor.execute('''
        INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)
    ''', ('User', 'Regular user managing their own vault'))
    cursor.execute('''
        INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)
    ''', ('Admin', 'System administrator'))
    cursor.execute('''
        INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)
    ''', ('Auditor', 'User who can only view audit logs'))

    cursor.execute('''
        INSERT OR IGNORE INTO categories (category_name, description) VALUES (?, ?)
    ''', ('Email', 'Email account credentials'))
    cursor.execute('''
        INSERT OR IGNORE INTO categories (category_name, description) VALUES (?, ?)
    ''', ('Social Media', 'Social media credentials'))
    cursor.execute('''
        INSERT OR IGNORE INTO categories (category_name, description) VALUES (?, ?)
    ''', ('Finance', 'Financial and banking credentials'))
    cursor.execute('''
        INSERT OR IGNORE INTO categories (category_name, description) VALUES (?, ?)
    ''', ('Other', 'Other types of credentials'))

    cursor.execute('''
        INSERT OR IGNORE INTO cipher_configs (algorithm_name, key_size, mode, description) VALUES (?, ?, ?, ?)
    ''', ('AES-GCM', 256, 'GCM', 'Advanced Encryption Standard 256-bit in Galois/Counter Mode'))
    cursor.execute('''
        INSERT OR IGNORE INTO cipher_configs (algorithm_name, key_size, mode, description) VALUES (?, ?, ?, ?)
    ''', ('TripleDES', 168, 'CBC', 'Triple Data Encryption Standard (legacy mode)'))

    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (1, 'REGISTER', 'User registered a new account'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (2, 'LOGIN_SUCCESS', 'User logged in successfully'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (3, 'LOGIN_FAILED', 'User failed to log in'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (4, 'VAULT_ADD', 'User added a new vault item'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (5, 'VAULT_VIEW', 'User viewed/decrypted a vault item'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (6, 'VAULT_UPDATE', 'User updated a vault item'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (7, 'VAULT_DELETE', 'User deleted a vault item'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (8, 'AUDIT_VIEW', 'Auditor viewed audit logs'))
    cursor.execute('''
        INSERT OR IGNORE INTO log_actions (action_id, action_name, description) VALUES (?, ?, ?)
    ''', (9, 'LOGOUT', 'User logged out'))

    conn.commit()
    conn.close()

