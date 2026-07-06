-- =========================================================================
-- ĐỒ ÁN/BÀI TẬP LỚN: SECURE PERSONAL DATA VAULT
-- TÊN HỆ THỐNG: FORTRESS VAULT (PHÁO ĐÀI BẢO MẬT DỮ LIỆU ĐA PHƯƠNG TIỆN)
-- CHUẨN HÓA CƠ SỞ DỮ LIỆU: THIRD NORMAL FORM (3NF) - PHIÊN BẢN SQL SERVER
-- =========================================================================

-- 1. Tạo Database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'FortressVault_Core')
BEGIN
    CREATE DATABASE FortressVault_Core;
END
GO

USE FortressVault_Core;
GO

-- =========================================================================
-- PHÂN HỆ 1: QUẢN LÝ TÀI KHOẢN, PHÂN QUYỀN & XÁC THỰC (Auth & RBAC)
-- =========================================================================

-- 1. Bảng Vai trò (Roles)
CREATE TABLE roles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    role_name VARCHAR(20) NOT NULL UNIQUE, -- 'ADMIN', 'PREMIUM_USER', 'STANDARD_USER'
    description NVARCHAR(255) NULL
);

-- 2. Bảng Người dùng gốc (Users)
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Sẽ được xử lý Hash bằng Bcrypt/Argon2 phía Python
    role_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    
    -- Ràng buộc CHECK thay thế cho ENUM trong SQL Server
    CONSTRAINT CHK_user_status CHECK (status IN ('ACTIVE', 'SUSPENDED', 'LOCKED')),
    CONSTRAINT FK_users_roles FOREIGN KEY (role_id) REFERENCES roles(id) ON UPDATE CASCADE
);

-- 3. Bảng Cấu hình Bảo mật Người dùng (User Security Profiles)
CREATE TABLE user_security_profiles (
    user_id INT PRIMARY KEY,
    -- Cặp khóa RSA dùng cho tính năng Chia sẻ dữ liệu bảo mật (Asymmetric Encryption)
    rsa_public_key VARCHAR(MAX) NOT NULL,
    rsa_encrypted_private_key VARCHAR(MAX) NOT NULL, -- Mã hóa bằng AES thông qua Master Password ở tầng Python
    -- Xác thực 2 lớp nâng cao (2FA)
    two_factor_secret VARCHAR(120) NULL,
    is_two_factor_enabled TINYINT DEFAULT 0,
    failed_login_attempts INT DEFAULT 0,
    lockout_until DATETIME NULL,
    
    CONSTRAINT FK_security_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================================================================
-- PHÂN HỆ 2: QUẢN LÝ DANH MỤC & KÉT SẮT DỮ LIỆU VĂN BẢN (Vault Credentials)
-- =========================================================================

-- 4. Bảng Danh mục (Categories)
CREATE TABLE categories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    category_name NVARCHAR(100) NOT NULL,
    icon_identifier VARCHAR(50) DEFAULT 'default-folder',
created_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_categories_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT UQ_user_category UNIQUE (user_id, category_name) -- Một user không được trùng tên danh mục
);

-- 5. Bảng Thuật toán và Chế độ mã hóa (Cipher Configurations)
CREATE TABLE cipher_configs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    algorithm_name VARCHAR(20) NOT NULL,  -- 'AES-256', 'TripleDES'
    encryption_mode VARCHAR(15) NOT NULL, -- 'CBC', 'GCM'
    key_size_bits INT NOT NULL,            
    CONSTRAINT UQ_cipher UNIQUE (algorithm_name, encryption_mode)
);

-- 6. Bảng Két sắt Thông tin nhạy cảm (Vault Credentials)
CREATE TABLE vault_credentials (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NULL,
    cipher_config_id INT NOT NULL, 
    title NVARCHAR(150) NOT NULL, -- Tên hiển thị gợi nhớ ở dạng văn bản rõ (Plaintext)
    
    -- Các trường thông tin nhạy cảm đã bị mã hóa hoàn toàn trước khi nạp xuống DB (dùng VARCHAR(MAX))
    encrypted_username VARCHAR(MAX) NULL,
    encrypted_password VARCHAR(MAX) NOT NULL,
    encrypted_notes VARCHAR(MAX) NULL,
    
    -- Vector khởi tạo (IV) ngẫu nhiên bắt buộc cho mỗi bản ghi dữ liệu
    iv VARCHAR(64) NOT NULL, 
    
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_vault_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT FK_vault_categories FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT FK_vault_configs FOREIGN KEY (cipher_config_id) REFERENCES cipher_configs(id) ON UPDATE CASCADE
);

-- =========================================================================
-- PHÂN HỆ 3: HỆ THỐNG LƯU TRỮ VÀ MÃ HÓA TỆP TIN NÂNG CAO (Secure File Vault)
-- =========================================================================

-- 7. Bảng Metadata của File (Vault Files)
CREATE TABLE vault_files (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NULL,
    cipher_config_id INT NOT NULL,
    file_name NVARCHAR(255) NOT NULL,       -- Tên file gốc ban đầu (Plaintext)
    file_extension VARCHAR(10) NOT NULL,   -- pdf, docx, png, zip
    file_size_bytes BIGINT NOT NULL,
    
    -- Đường dẫn vật lý đến file nhị phân đã bị mã hóa (.enc) trên thiết bị lưu trữ
    storage_path NVARCHAR(500) NOT NULL, 
    
    -- Khóa mật mã riêng của File (FEK) - Khóa này đã được Python mã hóa bọc bằng khóa Master của chủ sở hữu
    encrypted_file_key VARCHAR(MAX) NOT NULL, 
    iv VARCHAR(64) NOT NULL, -- Vector khởi tạo (IV) dành riêng cho File này
    
    created_at DATETIME DEFAULT GETDATE(),
updated_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_files_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT FK_files_categories FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT FK_files_configs FOREIGN KEY (cipher_config_id) REFERENCES cipher_configs(id) ON UPDATE CASCADE
);

-- =========================================================================
-- PHÂN HỆ 4: CHIA SẺ DỮ LIỆU AN TOÀN GIỮA CÁC TÀI KHOẢN (Secure Sharing System)
-- =========================================================================

-- 8. Bảng Quản lý chia sẻ dữ liệu (Secure Shares)
CREATE TABLE secure_shares (
    id INT IDENTITY(1,1) PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INT NOT NULL, -- ID của bản ghi mật khẩu hoặc file cụ thể
    
    -- Khóa giải mã được mã hóa bọc bảo vệ bằng RSA Public Key của người nhận (Receiver)
    encrypted_shared_key VARCHAR(MAX) NOT NULL, 
    permission_level VARCHAR(20) DEFAULT 'VIEW_ONLY',
    expires_at DATETIME NULL, -- Tính năng gia hạn thời gian tồn tại của phiên chia sẻ
    shared_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT CHK_share_target CHECK (target_type IN ('CREDENTIAL', 'FILE')),
    CONSTRAINT CHK_share_perm CHECK (permission_level IN ('VIEW_ONLY', 'ALLOW_EDIT')),
    -- SQL Server không cho phép ON DELETE CASCADE lặp vòng (Multiple Cascade Paths) 
    -- nên ở đây ta chuyển sender_id và receiver_id thành NO ACTION để tránh lỗi hệ thống.
    CONSTRAINT FK_shares_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT FK_shares_receiver FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE NO ACTION
);

-- =========================================================================
-- PHÂN HỆ 5: GIÁM SÁT HỆ THỐNG & NHẬT KÝ KIỂM TOÁN (Audit Logs & Monitoring)
-- =========================================================================

-- 9. Bảng Phân loại Hành động (Action Types)
CREATE TABLE log_actions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    action_code VARCHAR(50) NOT NULL UNIQUE, -- 'AUTH_LOGIN_SUCCESS', 'VAULT_DECRYPT_PASSWORD', etc.
    severity_level VARCHAR(15) DEFAULT 'INFO',
    description NVARCHAR(255) NULL,
    
    CONSTRAINT CHK_log_severity CHECK (severity_level IN ('INFO', 'WARNING', 'CRITICAL'))
);

-- 10. Bảng Nhật ký kiểm toán chính xác (Audit Logs)
CREATE TABLE audit_logs (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NULL, -- Để NULL nếu đối tượng bên ngoài tấn công/đăng nhập sai user không tồn tại
    action_id INT NOT NULL,
    ip_address VARCHAR(45) NOT NULL,  -- Hỗ trợ lưu trữ đầy đủ định dạng IPv4 và IPv6
user_agent VARCHAR(MAX) NOT NULL, -- Ghi nhận thông tin chi tiết trình duyệt/thiết bị thao tác
    action_details NVARCHAR(MAX) NULL, -- Mô tả cụ thể hành vi
    created_at DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT FK_logs_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT FK_logs_actions FOREIGN KEY (action_id) REFERENCES log_actions(id) ON UPDATE CASCADE
);
GO

-- =========================================================================
-- DỮ LIỆU CẤU HÌNH NỀN TẢNG BẮT BUỘC (SEED DATA)
-- =========================================================================

-- Chèn phân quyền tài khoản mặc định
INSERT INTO roles (role_name, description) VALUES 
('ADMIN', N'Quản trị viên toàn quyền cấu hình, theo dõi log hệ thống'),
('PREMIUM_USER', N'Người dùng cấp cao - Không giới hạn dung lượng lưu trữ tệp tin mã hóa'),
('STANDARD_USER', N'Người dùng tiêu chuẩn - Giới hạn tối đa 50MB dữ liệu tệp tin');

-- Chèn cấu hình mật mã học theo yêu cầu trực tiếp từ đề tài (AES & TripleDES)
INSERT INTO cipher_configs (algorithm_name, encryption_mode, key_size_bits) VALUES 
('AES', 'CBC', 256),
('AES', 'GCM', 256),
('TripleDES', 'CBC', 168);

-- Chèn danh mục mã hóa hành vi phục vụ hệ thống Audit Logs
INSERT INTO log_actions (action_code, severity_level, description) VALUES 
('AUTH_LOGIN_SUCCESS', 'INFO', N'Đăng nhập vào hệ thống Fortress Vault thành công'),
('AUTH_LOGIN_FAILED', 'WARNING', N'Thực hiện đăng nhập thất bại (Sai mật khẩu hoặc tài khoản)'),
('AUTH_2FA_CHALLENGE', 'INFO', N'Yêu cầu xác thực mã bảo mật 2 lớp (OTP)'),
('CREDENTIAL_CREATE', 'INFO', N'Tạo mới thông tin mật khẩu/tài khoản nhạy cảm đã mã hóa'),
('CREDENTIAL_DECRYPT_VIEW', 'INFO', N'Yêu cầu giải mã và hiển thị dữ liệu văn bản rõ'),
('FILE_ENCRYPT_UPLOAD', 'INFO', N'Mã hóa thành công và tải tệp tin bảo mật lên hệ thống'),
('FILE_DECRYPT_DOWNLOAD', 'INFO', N'Yêu cầu giải mã và tải tệp tin gốc về thiết bị'),
('SECURE_SHARE_GRANT', 'INFO', N'Cấp quyền chia sẻ dữ liệu bảo mật bằng cấu hình khóa RSA'),
('UNAUTHORIZED_INTERACTION', 'CRITICAL', N'Cảnh báo: Phát hiện hành vi cố tình truy cập trái phép dữ liệu không có quyền sở hữu');
GO
