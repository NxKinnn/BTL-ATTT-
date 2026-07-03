
import bcrypt
from typing import Optional, Dict, Any
from config.database import get_connection, row_to_dict
from core.crypto_vault import CryptoVault
from services.audit_service import AuditService


class AuthService:
    @staticmethod
    def hash_password(password: str) -> bytes:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    @staticmethod
    def check_password(password: str, password_hash: bytes) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)

    @staticmethod
    def register_user(
        username: str,
        password: str,
        role_name: str = "User",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Get role_id
            cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", (role_name,))
            role_row = cursor.fetchone()
            if not role_row:
                conn.close()
                return None
            role_id = role_row[0]

            # Check if username exists
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return None

            # Hash password
            password_hash = AuthService.hash_password(password)

            # Create user
            cursor.execute("""
                INSERT INTO users (username, password_hash, role_id)
                VALUES (?, ?, ?)
            """, (username, password_hash, role_id))
            user_id = cursor.lastrowid

            # Create security profile
            salt = CryptoVault.generate_salt()
            master_key = CryptoVault.derive_master_key(password, salt)
            private_key_pem, public_key_pem = CryptoVault.generate_rsa_key_pair()

            # Encrypt private key
            encrypted_private_key_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_private_key(private_key_pem, master_key)
            encrypted_private_key_full = f"{encrypted_private_key_hex}|{iv_hex}|{auth_tag_hex}"

            cursor.execute("""
                INSERT INTO user_security_profiles (
                    user_id, salt, encrypted_private_key, public_key, key_derivation_iterations
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                salt,
                encrypted_private_key_full,
                public_key_pem,
                CryptoVault.PBKDF2_ITERATIONS
            ))

            conn.commit()
            AuditService.log_event(user_id, 1, ip_address, user_agent, f"User {username} registered")
            return user_id
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def login_user(
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT u.*, r.role_name, usp.*
                FROM users u
                LEFT JOIN roles r ON u.role_id = r.role_id
                LEFT JOIN user_security_profiles usp ON u.user_id = usp.user_id
                WHERE u.username = ?
            """, (username,))
            row = cursor.fetchone()
            if not row:
                AuditService.log_event(None, 3, ip_address, user_agent, f"Login failed for user {username} (user not found)")
                return None

            user_data = row_to_dict(cursor, row)
            password_hash = user_data['password_hash']
            if not AuthService.check_password(password, password_hash):
                AuditService.log_event(user_data['user_id'], 3, ip_address, user_agent, f"Login failed for user {username} (wrong password)")
                return None

            AuditService.log_event(user_data['user_id'], 2, ip_address, user_agent, f"User {username} logged in")
            return user_data
        except Exception as e:
            print(f"Error logging in user: {str(e)}")
            return None
        finally:
            conn.close()

    @staticmethod
    def logout_user(
        user_id: Optional[int],
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log a logout event"""
        AuditService.log_event(
            user_id,
            9,  # Let's use 9 for LOGOUT (we need to add to setup)
            ip_address,
            user_agent,
            f"User {username or 'unknown'} logged out"
        )

