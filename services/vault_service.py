
"""
Vault Service for FortressVault
Handles all vault operations with AES-256-GCM encryption
"""
import json
from typing import Optional, List, Dict, Any
from config.database import execute_query, execute_non_query
from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError
from services.audit_service import AuditService

class VaultService:
    @staticmethod
    def add_vault_item(
        user_id: int,
        item_name: str,
        master_key: bytes,
        username: Optional[str] = None,
        password: Optional[str] = None,
        notes: Optional[str] = None,
        category_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """
        Add a new encrypted vault item
        Returns vault_id if successful
        """
        # Create JSON object of sensitive data
        sensitive_data = {
            "username": username,
            "password": password,
            "notes": notes
        }
        sensitive_json = json.dumps(sensitive_data)
        
        # Encrypt with AES-256-GCM (nonce random)
        encrypted_data, iv, auth_tag = CryptoVault.encrypt_aes_gcm(sensitive_json, master_key)
        
        # Get default AES-GCM cipher config
        cipher_configs = execute_query("SELECT cipher_config_id FROM cipher_configs WHERE algorithm_name = 'AES-GCM'")
        if not cipher_configs:
            return None
        cipher_config_id = cipher_configs[0]['cipher_config_id']
        
        # Insert into database
        vault_id = execute_non_query("""
            INSERT INTO vault_credentials (
                user_id, category_id, item_name, encrypted_password, iv, auth_tag, cipher_config_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (user_id, category_id, item_name, encrypted_data, iv, auth_tag, cipher_config_id), return_id=True)
        
        if vault_id:
            AuditService.log_event(user_id, 4, ip_address, user_agent, f"Added vault item: {item_name}")
        
        return vault_id
    
    @staticmethod
    def get_user_vault_items(user_id: int, role: str) -> List[Dict[str, Any]]:
        """
        Get list of vault items for a user (only metadata, no decrypted data)
        """
        if role != "User":
            return []
        
        return execute_query("""
            SELECT vc.vault_id, vc.user_id, vc.category_id, vc.item_name, vc.created_at, vc.updated_at, c.category_name
            FROM vault_credentials vc
            LEFT JOIN categories c ON vc.category_id = c.category_id
            WHERE vc.user_id = ?
            ORDER BY vc.created_at DESC
        """, (user_id,))
    
    @staticmethod
    def decrypt_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        master_key: bytes,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Decrypt a vault item
        Returns decrypted data or None if error/permissions denied
        """
        if role != "User":
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Permission denied: Attempt to decrypt vault item {vault_id}")
            return None
        
        # Get encrypted data
        items = execute_query("""
            SELECT vc.vault_id, vc.user_id, vc.item_name, vc.encrypted_password, vc.iv, vc.auth_tag
            FROM vault_credentials vc
            WHERE vc.vault_id = ? AND vc.user_id = ?
        """, (vault_id, user_id))
        
        if not items:
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Vault item {vault_id} not found")
            return None
        
        item = items[0]
        
        try:
            # Decrypt
            decrypted_json = CryptoVault.decrypt_aes_gcm(
                item['encrypted_password'],
                item['iv'],
                item['auth_tag'],
                master_key
            )
            sensitive_data = json.loads(decrypted_json)
            
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Decrypted vault item: {item['item_name']}")
            
            return {
                "vault_id": item['vault_id'],
                "item_name": item['item_name'],
                "username": sensitive_data.get('username'),
                "password": sensitive_data.get('password'),
                "notes": sensitive_data.get('notes')
            }
        except (IntegrityError, DecryptionError, json.JSONDecodeError) as e:
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Decryption failed for vault item {vault_id}: {str(e)}")
            return None
    
    @staticmethod
    def update_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        master_key: bytes,
        item_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Update a vault item
        Returns True if successful
        """
        if role != "User":
            return False
        
        # Get current encrypted data
        items = execute_query("""
            SELECT vc.encrypted_password, vc.iv, vc.auth_tag
            FROM vault_credentials vc
            WHERE vc.vault_id = ? AND vc.user_id = ?
        """, (vault_id, user_id))
        
        if not items:
            return False
        
        try:
            # Decrypt current data
            decrypted_json = CryptoVault.decrypt_aes_gcm(
                items[0]['encrypted_password'],
                items[0]['iv'],
                items[0]['auth_tag'],
                master_key
            )
            current_data = json.loads(decrypted_json)
            
            # Update fields
            updated_data = current_data.copy()
            if username is not None:
                updated_data['username'] = username
            if password is not None:
                updated_data['password'] = password
            if notes is not None:
                updated_data['notes'] = notes
            
            # Re-encrypt
            updated_json = json.dumps(updated_data)
            encrypted_data, new_iv, new_auth_tag = CryptoVault.encrypt_aes_gcm(updated_json, master_key)
            
            # Prepare update query
            if item_name:
                execute_non_query("""
                    UPDATE vault_credentials
                    SET item_name = ?, encrypted_password = ?, iv = ?, auth_tag = ?, updated_at = GETDATE()
                    WHERE vault_id = ? AND user_id = ?
                """, (item_name, encrypted_data, new_iv, new_auth_tag, vault_id, user_id))
            else:
                execute_non_query("""
                    UPDATE vault_credentials
                    SET encrypted_password = ?, iv = ?, auth_tag = ?, updated_at = GETDATE()
                    WHERE vault_id = ? AND user_id = ?
                """, (encrypted_data, new_iv, new_auth_tag, vault_id, user_id))
            
            AuditService.log_event(user_id, 6, ip_address, user_agent, f"Updated vault item: {vault_id}")
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Delete a vault item
        Returns True if successful
        """
        if role != "User":
            return False
        
        count = execute_non_query("""
            DELETE FROM vault_credentials WHERE vault_id = ? AND user_id = ?
        """, (vault_id, user_id))
        
        if count:
            AuditService.log_event(user_id, 7, ip_address, user_agent, f"Deleted vault item: {vault_id}")
            return True
        return False
    
    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        """Get all categories"""
        return execute_query("SELECT category_id, category_name, description FROM categories ORDER BY category_id")

