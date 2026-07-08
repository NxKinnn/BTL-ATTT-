
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
        user_agent: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        identity_number: Optional[str] = None,
        algorithm: Optional[str] = "AES-256-GCM"
    ) -> Optional[int]:
        """
        Add a new encrypted vault item
        Returns vault_id if successful
        """
        # Create JSON object of sensitive data
        sensitive_data = {
            "title": item_name,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "identity_number": identity_number,
            "username": username or "",
            "password": password or "",
            "notes": notes,
            "note": notes,
            "algorithm": algorithm or "AES-256-GCM"
        }
        sensitive_json = json.dumps(sensitive_data)
        
        # Encrypt with AES-256-GCM (nonce random)
        encrypted_data, iv, auth_tag = CryptoVault.encrypt_aes_gcm(sensitive_json, master_key)
        
        # Get default AES-GCM cipher config
        algo_query = "AES-GCM" if "AES" in (algorithm or "") else "TripleDES"
        cipher_configs = execute_query("SELECT cipher_config_id FROM cipher_configs WHERE algorithm_name LIKE ?", (f"%{algo_query}%",))
        if not cipher_configs:
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
        Admin sees system-wide metadata and ciphertext preview
        """
        if role == "Admin":
            return execute_query("""
                SELECT vc.vault_id, vc.user_id, u.username as owner, u.username, vc.item_name as title, vc.item_name, vc.created_at, vc.updated_at, c.category_name, cc.algorithm_name as algorithm, SUBSTRING(vc.encrypted_password, 1, 32) + '...' as ciphertext_preview
                FROM vault_credentials vc
                LEFT JOIN users u ON vc.user_id = u.user_id
                LEFT JOIN categories c ON vc.category_id = c.category_id
                LEFT JOIN cipher_configs cc ON vc.cipher_config_id = cc.cipher_config_id
                ORDER BY vc.created_at DESC
            """)
        elif role != "User":
            return []
        
        return execute_query("""
            SELECT vc.vault_id, vc.user_id, vc.category_id, vc.item_name, vc.created_at, vc.updated_at, c.category_name, cc.algorithm_name as algorithm
            FROM vault_credentials vc
            LEFT JOIN categories c ON vc.category_id = c.category_id
            LEFT JOIN cipher_configs cc ON vc.cipher_config_id = cc.cipher_config_id
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
            SELECT vc.vault_id, vc.user_id, vc.item_name, vc.encrypted_password, vc.iv, vc.auth_tag, vc.created_at, cc.algorithm_name as algorithm
            FROM vault_credentials vc
            LEFT JOIN cipher_configs cc ON vc.cipher_config_id = cc.cipher_config_id
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
                "title": sensitive_data.get('title') or item['item_name'],
                "full_name": sensitive_data.get('full_name') or "",
                "email": sensitive_data.get('email') or "",
                "phone": sensitive_data.get('phone') or "",
                "identity_number": sensitive_data.get('identity_number') or "",
                "username": sensitive_data.get('username') or "",
                "password": sensitive_data.get('password') or "",
                "notes": sensitive_data.get('notes') or sensitive_data.get('note') or "",
                "note": sensitive_data.get('note') or sensitive_data.get('notes') or "",
                "algorithm": item.get('algorithm') or sensitive_data.get('algorithm') or "AES-256-GCM",
                "created_at": str(item['created_at']) if item.get('created_at') else None
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
        user_agent: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        identity_number: Optional[str] = None
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
                updated_data['note'] = notes
            if full_name is not None:
                updated_data['full_name'] = full_name
            if email is not None:
                updated_data['email'] = email
            if phone is not None:
                updated_data['phone'] = phone
            if identity_number is not None:
                updated_data['identity_number'] = identity_number
            if item_name is not None:
                updated_data['title'] = item_name
            
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
        
        # First verify the item exists and belongs to this user
        items = execute_query(
            "SELECT vault_id FROM vault_credentials WHERE vault_id = ? AND user_id = ?",
            (vault_id, user_id)
        )
        if not items:
            return False
        
        execute_non_query("""
            DELETE FROM vault_credentials WHERE vault_id = ? AND user_id = ?
        """, (vault_id, user_id))
        
        AuditService.log_event(user_id, 7, ip_address, user_agent, f"Deleted vault item: {vault_id}")
        return True
    
    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        """Get all categories"""
        return execute_query("SELECT category_id, category_name, description FROM categories ORDER BY category_id")

