
import os
import bcrypt
from datetime import datetime
from config.sql_server_config import get_sql_server_connection
from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError


class FortressVaultService:
    # Action IDs for audit_logs
    ACTION_REGISTER = 1
    ACTION_LOGIN_SUCCESS = 2
    ACTION_LOGIN_FAILED = 3
    ACTION_ADD_VAULT = 4
    ACTION_VIEW_VAULT_SUCCESS = 5
    ACTION_VIEW_VAULT_FAILED = 6
    ACTION_ADMIN_GRANT_PERMISSION = 7  # If needed later

    def __init__(self):
        pass

    def register_user(
        self,
        username: str,
        password: str,
        role_name: str,
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device"
    ) -> int:
        """
        Đăng ký người dùng mới, hash mật khẩu bằng bcrypt,
        và tạo user_security_profiles với salt ngẫu nhiên
        """
        if role_name not in ["User", "Admin", "Auditor"]:
            raise ValueError("Invalid role! Must be User, Admin, or Auditor.")

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        try:
            # 1. Get role_id from roles table
            cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", role_name)
            role_row = cursor.fetchone()
            if not role_row:
                raise ValueError(f"Role '{role_name}' not found in database!")
            role_id = role_row[0]

            # 2. Hash password using bcrypt
            password_bytes = password.encode("utf-8")
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)

            # 3. Insert into users table
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, GETDATE(), GETDATE());
                SELECT SCOPE_IDENTITY();
                """,
                (username, password_hash, role_id)
            )
            user_id = cursor.fetchone()[0]

            # 4. Generate salt for user_security_profiles (stored in DB, not the key!)
            user_salt = os.urandom(16)

            # 5. Insert into user_security_profiles table
            cursor.execute(
                """
                INSERT INTO user_security_profiles (user_id, salt, key_derivation_iterations, created_at, updated_at)
                VALUES (?, ?, ?, GETDATE(), GETDATE());
                """,
                (user_id, user_salt, CryptoVault.PBKDF2_ITERATIONS)
            )

            # 6. Log the registration in audit_logs (if needed)
            cursor.execute(
                """
                INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE());
                """,
                (self.ACTION_REGISTER, user_id, ip_address, device_info, f"User '{username}' registered with role '{role_name}'")
            )

            conn.commit()
            return user_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def login_user(
        self,
        username: str,
        password: str,
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device"
    ) -> dict:
        """
        Đăng nhập người dùng, kiểm tra mật khẩu, và trả về thông tin user + salt
        """
        conn = get_sql_server_connection()
        cursor = conn.cursor()

        try:
            # 1. Get user info from users table
            cursor.execute(
                """
                SELECT u.user_id, u.password_hash, u.role_id, r.role_name
                FROM users u
                INNER JOIN roles r ON u.role_id = r.role_id
                WHERE u.username = ? AND u.is_active = 1;
                """,
                (username,)
            )
            user_row = cursor.fetchone()

            if not user_row:
                # Log failed login attempt (no user found)
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_LOGIN_FAILED, ip_address, device_info, f"Failed login attempt for username '{username}' (user not found)")
                )
                conn.commit()
                raise ValueError("Invalid username or password!")

            user_id, password_hash_db, role_id, role_name = user_row

            # 2. Check password
            password_bytes = password.encode("utf-8")
            if not bcrypt.checkpw(password_bytes, password_hash_db):
                # Log failed login attempt (wrong password)
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_LOGIN_FAILED, user_id, ip_address, device_info, f"Failed login attempt for username '{username}' (wrong password)")
                )
                conn.commit()
                raise ValueError("Invalid username or password!")

            # 3. Get user's salt from user_security_profiles
            cursor.execute(
                """
                SELECT salt, key_derivation_iterations
                FROM user_security_profiles
                WHERE user_id = ?;
                """,
                (user_id,)
            )
            security_row = cursor.fetchone()
            if not security_row:
                raise ValueError("User security profile not found!")

            user_salt, key_iterations = security_row

            # 4. Log successful login
            cursor.execute(
                """
                INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE());
                """,
                (self.ACTION_LOGIN_SUCCESS, user_id, ip_address, device_info, f"User '{username}' logged in successfully")
            )
            conn.commit()

            return {
                "user_id": user_id,
                "username": username,
                "role_id": role_id,
                "role_name": role_name,
                "user_salt": user_salt,
                "key_iterations": key_iterations
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def add_vault_item(
        self,
        user_id: int,
        role_name: str,
        master_password: str,
        user_salt: bytes,
        item_name: str,
        item_username: str,
        item_password: str,
        item_url: str = None,
        item_notes: str = None,
        category_id: int = None,
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device"
    ) -> int:
        """
        User thêm dữ liệu vào vault: mã hóa bằng AES-GCM và lưu vào vault_credentials
        Chỉ User role mới được phép!
        """
        if role_name != "User":
            raise PermissionError("Only User role can add vault items!")

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        try:
            # 1. Derive AES key from master password + user salt
            aes_key = CryptoVault.derive_master_key(master_password, user_salt, key_length=32)

            # 2. Combine all sensitive data into a single plaintext string
            plaintext = f"Username: {item_username}\nPassword: {item_password}\nURL: {item_url or 'N/A'}\nNotes: {item_notes or 'N/A'}"

            # 3. Encrypt using AES-GCM
            ciphertext_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_aes_gcm(plaintext, aes_key)

            # 4. Get default cipher config (AES-GCM 256-bit)
            cursor.execute("SELECT TOP 1 cipher_config_id FROM cipher_configs WHERE algorithm_name = 'AES-GCM' AND key_size = 256;")
            config_row = cursor.fetchone()
            cipher_config_id = config_row[0] if config_row else None
            if not cipher_config_id:
                raise ValueError("AES-GCM cipher config not found!")

            # 5. Insert into vault_credentials
            cursor.execute(
                """
                INSERT INTO vault_credentials (
                    user_id, category_id, item_name, encrypted_data, iv, auth_tag,
                    cipher_config_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE());
                SELECT SCOPE_IDENTITY();
                """,
                (user_id, category_id, item_name, ciphertext_hex, iv_hex, auth_tag_hex, cipher_config_id)
            )
            vault_item_id = cursor.fetchone()[0]

            # 6. Log the action
            cursor.execute(
                """
                INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE());
                """,
                (self.ACTION_ADD_VAULT, user_id, ip_address, device_info, f"User added vault item '{item_name}' (ID: {vault_item_id})")
            )

            conn.commit()
            return vault_item_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def view_vault_item(
        self,
        user_id: int,
        role_name: str,
        vault_item_id: int,
        master_password: str,
        user_salt: bytes,
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device"
    ) -> dict:
        """
        User xem dữ liệu vault của mình, giải mã và trả về.
        Mỗi lần gọi phải ghi vào audit_logs!
        Admin không thể xem!
        """
        conn = get_sql_server_connection()
        cursor = conn.cursor()

        try:
            # 1. Check role: only User can view their own vault items!
            if role_name != "User":
                # Log failed view attempt (wrong role)
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_VIEW_VAULT_FAILED, user_id, ip_address, device_info, f"Failed to view vault item {vault_item_id}: insufficient permissions (role: {role_name})")
                )
                conn.commit()
                raise PermissionError("Only User role can view vault items!")

            # 2. Get vault item from DB
            cursor.execute(
                """
                SELECT user_id, encrypted_data, iv, auth_tag, item_name
                FROM vault_credentials
                WHERE vault_credential_id = ?;
                """,
                (vault_item_id,)
            )
            vault_row = cursor.fetchone()

            if not vault_row:
                # Log failed view attempt (item not found)
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_VIEW_VAULT_FAILED, user_id, ip_address, device_info, f"Failed to view vault item {vault_item_id}: item not found")
                )
                conn.commit()
                raise ValueError("Vault item not found!")

            item_user_id, ciphertext_hex, iv_hex, auth_tag_hex, item_name = vault_row

            # 3. Check if item belongs to current user
            if item_user_id != user_id:
                # Log failed view attempt (not owner)
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_VIEW_VAULT_FAILED, user_id, ip_address, device_info, f"Failed to view vault item {vault_item_id}: not the owner")
                )
                conn.commit()
                raise PermissionError("You do not have permission to view this vault item!")

            # 4. Derive AES key
            aes_key = CryptoVault.derive_master_key(master_password, user_salt, key_length=32)

            # 5. Decrypt the data
            try:
                decrypted_plaintext = CryptoVault.decrypt_aes_gcm(ciphertext_hex, iv_hex, auth_tag_hex, aes_key)
            except (IntegrityError, DecryptionError) as e:
                # Log failed decryption
                cursor.execute(
                    """
                    INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                    VALUES (?, ?, ?, ?, ?, GETDATE());
                    """,
                    (self.ACTION_VIEW_VAULT_FAILED, user_id, ip_address, device_info, f"Failed to decrypt vault item {vault_item_id}: {str(e)}")
                )
                conn.commit()
                raise e

            # 6. Log successful view
            cursor.execute(
                """
                INSERT INTO audit_logs (action_id, user_id, ip_address, device_info, action_details, created_at)
                VALUES (?, ?, ?, ?, ?, GETDATE());
                """,
                (self.ACTION_VIEW_VAULT_SUCCESS, user_id, ip_address, device_info, f"Successfully viewed vault item '{item_name}' (ID: {vault_item_id})")
            )
            conn.commit()

            # 7. Parse decrypted plaintext into structured data
            parsed_data = {}
            for line in decrypted_plaintext.split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    parsed_data[key] = value

            return {
                "vault_item_id": vault_item_id,
                "item_name": item_name,
                "decrypted_data": parsed_data
            }

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def auditor_view_logs(
        self,
        user_id: int,
        role_name: str,
        page_number: int = 1,
        page_size: int = 20,
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device"
    ) -> list:
        """
        Auditor xem audit logs, không được phép xem vault_credentials!
        """
        if role_name != "Auditor":
            raise PermissionError("Only Auditor role can view audit logs!")

        conn = get_sql_server_connection()
        cursor = conn.cursor()

        try:
            offset = (page_number - 1) * page_size

            cursor.execute(
                """
                SELECT al.audit_log_id, al.action_id, la.action_name, al.user_id, u.username,
                       al.ip_address, al.device_info, al.action_details, al.created_at
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.user_id
                LEFT JOIN log_actions la ON al.action_id = la.action_id
                ORDER BY al.created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
                """,
                (offset, page_size)
            )
            logs = cursor.fetchall()

            # Convert to list of dictionaries
            log_list = []
            columns = [column[0] for column in cursor.description]
            for log_row in logs:
                log_dict = dict(zip(columns, log_row))
                # Convert datetime to string for readability
                if log_dict.get("created_at"):
                    log_dict["created_at"] = log_dict["created_at"].isoformat()
                log_list.append(log_dict)

            return log_list

        except Exception as e:
            raise e
        finally:
            cursor.close()
            conn.close()

