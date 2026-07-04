
"""
Authentication Service for FortressVault
Handles user registration, login, logout, and JWT management
"""
import bcrypt
from typing import Optional, Dict, Any
from config.database import execute_query, execute_non_query
from core.crypto_vault import CryptoVault
from services.audit_service import AuditService

class AuthService:
    @staticmethod
    def hash_password(password: str) -> bytes:
        """Hash a password using bcrypt with salt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    @staticmethod
    def check_password(password: str, password_hash: bytes) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    
    @staticmethod
    def register_user(
        username: str,
        password: str,
        role_name: str = "User",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """
        Register a new user
        Returns user_id if successful, None if user already exists or error
        """
        # Check if username already exists
        existing = execute_query("SELECT user_id FROM users WHERE username = ?", (username,))
        if existing:
            return None
        
        # Get role_id from role_name
        roles = execute_query("SELECT role_id FROM roles WHERE role_name = ?", (role_name,))
        if not roles:
            return None
        role_id = roles[0]['role_id']
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Insert new user
        user_id = execute_non_query(
            "INSERT INTO users (username, password_hash, role_id, is_active, created_at, updated_at) VALUES (?, ?, ?, 1, GETDATE(), GETDATE())",
            (username, password_hash, role_id),
            return_id=True
        )
        if not user_id:
            return None
        
        # Generate and save user security profile
        salt = CryptoVault.generate_salt()
        master_key = CryptoVault.derive_master_key(password, salt)
        private_key_pem, public_key_pem = CryptoVault.generate_rsa_key_pair()
        
        # Encrypt private key with master key
        encrypted_private_key_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_private_key(private_key_pem, master_key)
        encrypted_private_key_full = f"{encrypted_private_key_hex}|{iv_hex}|{auth_tag_hex}"
        
        execute_non_query("""
            INSERT INTO user_security_profiles (user_id, salt, encrypted_private_key, public_key, key_derivation_iterations, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (user_id, salt, encrypted_private_key_full, public_key_pem, CryptoVault.PBKDF2_ITERATIONS))
        
        # Log registration event
        AuditService.log_event(user_id, 1, ip_address, user_agent, f"User {username} registered successfully")
        
        return user_id
    
    @staticmethod
    def login_user(
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user
        Returns user data if successful, None if failed
        """
        # Get user data
        users = execute_query("""
            SELECT u.user_id, u.username, u.password_hash, u.is_active, u.role_id, r.role_name, usp.salt
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            LEFT JOIN user_security_profiles usp ON u.user_id = usp.user_id
            WHERE u.username = ?
        """, (username,))
        
        if not users:
            AuditService.log_event(None, 3, ip_address, user_agent, f"Login failed: User {username} not found")
            return None
        
        user = users[0]
        
        # Check if user is active
        if not user['is_active']:
            AuditService.log_event(user['user_id'], 3, ip_address, user_agent, f"Login failed: User {username} is inactive")
            return None
        
        # Check password
        if not AuthService.check_password(password, user['password_hash']):
            AuditService.log_event(user['user_id'], 3, ip_address, user_agent, f"Login failed: Wrong password for {username}")
            return None
        
        # Log successful login
        AuditService.log_event(user['user_id'], 2, ip_address, user_agent, f"User {username} logged in successfully")
        
        return user
    
    @staticmethod
    def logout_user(
        user_id: Optional[int],
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log a logout event"""
        AuditService.log_event(user_id, 9, ip_address, user_agent, f"User {username or 'unknown'} logged out")

