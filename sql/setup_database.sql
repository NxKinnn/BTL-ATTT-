
USE [master];
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'FortressVault_Core')
BEGIN
    ALTER DATABASE [FortressVault_Core] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [FortressVault_Core];
END
GO

CREATE DATABASE [FortressVault_Core];
GO

USE [FortressVault_Core];
GO

CREATE TABLE roles (
    role_id INT IDENTITY(1,1) PRIMARY KEY,
    role_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(255)
);

CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) NOT NULL UNIQUE,
    password_hash VARBINARY(255) NOT NULL,
    role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

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

CREATE TABLE categories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name NVARCHAR(100) NOT NULL UNIQUE,
    description NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE cipher_configs (
    cipher_config_id INT IDENTITY(1,1) PRIMARY KEY,
    algorithm_name NVARCHAR(50) NOT NULL,
    key_size INT NOT NULL,
    mode NVARCHAR(50) NOT NULL,
    description NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);

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

CREATE TABLE log_actions (
    action_id INT PRIMARY KEY,
    action_name NVARCHAR(100) NOT NULL UNIQUE,
    description NVARCHAR(255)
);

CREATE TABLE audit_logs (
    audit_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    action_id INT NOT NULL FOREIGN KEY REFERENCES log_actions(action_id),
    user_id INT NULL FOREIGN KEY REFERENCES users(user_id),
    ip_address NVARCHAR(50),
    user_agent NVARCHAR(255),
    action_details NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE()
);

-- Insert default data
INSERT INTO roles (role_name, description) VALUES
    (N'User', N'Regular user managing their own vault'),
    (N'Admin', N'System administrator'),
    (N'Auditor', N'User who can only view audit logs');

INSERT INTO categories (category_name, description) VALUES
    (N'Email', N'Email account credentials'),
    (N'Social Media', N'Social media credentials'),
    (N'Finance', N'Financial and banking credentials'),
    (N'Other', N'Other types of credentials');

INSERT INTO cipher_configs (algorithm_name, key_size, mode, description) VALUES
    (N'AES-GCM', 256, N'GCM', N'Advanced Encryption Standard 256-bit in Galois/Counter Mode'),
    (N'TripleDES', 168, N'CBC', N'Triple Data Encryption Standard (legacy mode)');

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
GO

PRINT 'Database setup complete!';
GO

