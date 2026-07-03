
import json
from typing import Optional, List, Dict, Any
from config.database import get_connection, row_to_dict
from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError
from services.audit_service import AuditService


class VaultService:
    @staticmethod
    def add_vault_item(
        user_id: int,
        item_name: str,
        user_salt: Optional[bytes] = None,
        master_password: Optional[str] = None,
        master_key: Optional[bytes] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        notes: Optional[str] = None,
        category_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Get master key
            if master_key is not None:
                key = master_key
            elif master_password is not None and user_salt is not None:
                key = CryptoVault.derive_master_key(master_password, user_salt)
            else:
                raise ValueError("Either master_key or both master_password and user_salt must be provided!")

            # Create a single data object to encrypt all fields together
            sensitive_data = {
                "username": username,
                "password": password,
                "notes": notes
            }
            sensitive_json = json.dumps(sensitive_data)

            # Encrypt the single JSON blob
            encrypted_data, iv, auth_tag = CryptoVault.encrypt_aes_gcm(sensitive_json, key)

            # Get cipher config id
            cursor.execute("SELECT cipher_config_id FROM cipher_configs WHERE algorithm_name = 'AES-GCM'")
            config_row = cursor.fetchone()
            if not config_row:
                conn.close()
                return None
            cipher_config_id = config_row[0]

            # Insert vault item
            cursor.execute("""
                INSERT INTO vault_credentials (
                    user_id, category_id, item_name, encrypted_password, iv, auth_tag, cipher_config_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                category_id,
                item_name,
                encrypted_data,
                iv,
                auth_tag,
                cipher_config_id
            ))
            vault_id = cursor.lastrowid
            conn.commit()
            AuditService.log_event(user_id, 4, ip_address, user_agent, f"Added vault item: {item_name}")
            return vault_id
        except Exception as e:
            conn.rollback()
            print(f"Error adding vault item: {str(e)}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_vault_items(user_id: int, role: str) -> List[Dict[str, Any]]:
        if role != 'User':
            return []

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vc.*, c.category_name
            FROM vault_credentials vc
            LEFT JOIN categories c ON vc.category_id = c.category_id
            WHERE vc.user_id = ?
            ORDER BY vc.created_at DESC
        """, (user_id,))

        items = []
        for row in cursor.fetchall():
            item = row_to_dict(cursor, row)
            items.append(item)

        conn.close()
        return items

    @staticmethod
    def decrypt_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        user_salt: Optional[bytes] = None,
        master_password: Optional[str] = None,
        master_key: Optional[bytes] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if role != 'User':
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Attempt to decrypt vault item {vault_id} denied (role: {role})")
            return None

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM vault_credentials WHERE vault_id = ? AND user_id = ?", (vault_id, user_id))
            row = cursor.fetchone()
            if not row:
                AuditService.log_event(user_id, 5, ip_address, user_agent, f"Vault item {vault_id} not found")
                return None

            item = row_to_dict(cursor, row)
            
            # Get master key
            if master_key is not None:
                key = master_key
            elif master_password is not None and user_salt is not None:
                key = CryptoVault.derive_master_key(master_password, user_salt)
            else:
                raise ValueError("Either master_key or both master_password and user_salt must be provided!")

            # Decrypt the JSON blob
            decrypted_json = CryptoVault.decrypt_aes_gcm(item['encrypted_password'], item['iv'], item['auth_tag'], key)
            sensitive_data = json.loads(decrypted_json)

            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Decrypted vault item: {item['item_name']}")
            return {
                'vault_id': item['vault_id'],
                'item_name': item['item_name'],
                'username': sensitive_data.get('username'),
                'password': sensitive_data.get('password'),
                'notes': sensitive_data.get('notes')
            }
        except (IntegrityError, DecryptionError, json.JSONDecodeError) as e:
            AuditService.log_event(user_id, 5, ip_address, user_agent, f"Decryption failed for vault item {vault_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error decrypting vault item: {str(e)}")
            return None
        finally:
            conn.close()

    @staticmethod
    def update_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        user_salt: Optional[bytes] = None,
        master_password: Optional[str] = None,
        master_key: Optional[bytes] = None,
        item_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        if role != 'User':
            return False

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM vault_credentials WHERE vault_id = ? AND user_id = ?", (vault_id, user_id))
            existing_item = cursor.fetchone()
            if not existing_item:
                return False

            item_dict = row_to_dict(cursor, existing_item)

            # Get master key
            if master_key is not None:
                key = master_key
            elif master_password is not None and user_salt is not None:
                key = CryptoVault.derive_master_key(master_password, user_salt)
            else:
                raise ValueError("Either master_key or both master_password and user_salt must be provided!")

            # First decrypt existing data to get current values
            decrypted_json = CryptoVault.decrypt_aes_gcm(item_dict['encrypted_password'], item_dict['iv'], item_dict['auth_tag'], key)
            current_data = json.loads(decrypted_json)

            # Update only provided fields
            updated_data = current_data.copy()
            if username is not None:
                updated_data['username'] = username
            if password is not None:
                updated_data['password'] = password
            if notes is not None:
                updated_data['notes'] = notes

            # Encrypt updated data
            updated_json = json.dumps(updated_data)
            encrypted_data, iv, auth_tag = CryptoVault.encrypt_aes_gcm(updated_json, key)

            # Prepare update statement
            update_fields = []
            update_values = []

            if item_name:
                update_fields.append("item_name = ?")
                update_values.append(item_name)

            update_fields.extend(["encrypted_password = ?", "iv = ?", "auth_tag = ?", "updated_at = GETDATE()"])
            update_values.extend([encrypted_data, iv, auth_tag, vault_id, user_id])

            update_query = f"UPDATE vault_credentials SET {', '.join(update_fields)} WHERE vault_id = ? AND user_id = ?"
            cursor.execute(update_query, update_values)
            conn.commit()
            AuditService.log_event(user_id, 6, ip_address, user_agent, f"Updated vault item: {vault_id}")
            return True
        except Exception as e:
            print(f"Error updating vault item: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_vault_item(
        user_id: int,
        role: str,
        vault_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        if role != 'User':
            return False

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM vault_credentials WHERE vault_id = ? AND user_id = ?", (vault_id, user_id))
            conn.commit()
            AuditService.log_event(user_id, 7, ip_address, user_agent, f"Deleted vault item: {vault_id}")
            return True
        except Exception as e:
            print(f"Error deleting vault item: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY category_id")
        categories = []
        for row in cursor.fetchall():
            categories.append(row_to_dict(cursor, row))
        conn.close()
        return categories

