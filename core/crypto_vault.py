
import os
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Dict, Any


class CryptoVaultError(Exception):
    pass


class IntegrityError(CryptoVaultError):
    pass


class DecryptionError(CryptoVaultError):
    pass


class CryptoVault:
    PBKDF2_ITERATIONS = 100000
    AES_KEY_SIZE = 32  # 256 bits
    SALT_SIZE = 16  # 128 bits
    AES_IV_SIZE = 12  # 96 bits (for GCM)
    TRIPLEDES_KEY_SIZE = 24  # 168 bits (3 keys of 56 bits each)
    TRIPLEDES_IV_SIZE = 8  # 64 bits for CBC

    @staticmethod
    def derive_master_key(master_password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS, key_size: int = AES_KEY_SIZE) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_size,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(master_password.encode('utf-8'))

    @staticmethod
    def encrypt_aes_gcm(plaintext: str, key: bytes) -> Tuple[str, str, str]:
        iv = os.urandom(CryptoVault.AES_IV_SIZE)
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()
        ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
        return (
            ciphertext.hex(),
            iv.hex(),
            encryptor.tag.hex()
        )

    @staticmethod
    def decrypt_aes_gcm(ciphertext_hex: str, iv_hex: str, auth_tag_hex: str, key: bytes) -> str:
        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
            iv = bytes.fromhex(iv_hex)
            auth_tag = bytes.fromhex(auth_tag_hex)

            decryptor = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            ).decryptor()

            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext_bytes.decode('utf-8')
        except ValueError as e:
            raise DecryptionError(f"Decryption failed: {str(e)}") from e
        except Exception as e:
            if hasattr(e, '__class__') and 'InvalidTag' in str(e.__class__.__name__):
                raise IntegrityError("Data tampered or invalid key") from e
            raise DecryptionError(f"Decryption failed: {str(e)}") from e

    @staticmethod
    def encrypt_3des_cbc(plaintext: str, key: bytes) -> Tuple[str, str]:
        """Encrypt using TripleDES in CBC mode (for legacy/comparison only!)"""
        if len(key) != CryptoVault.TRIPLEDES_KEY_SIZE:
            raise ValueError(f"3DES key must be 24 bytes long, got {len(key)}")
        
        iv = os.urandom(CryptoVault.TRIPLEDES_IV_SIZE)
        padder = padding.PKCS7(64).padder()  # 3DES uses 64-bit block size
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        encryptor = Cipher(
            algorithms.TripleDES(key),
            modes.CBC(iv),
            backend=default_backend()
        ).encryptor()
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return (ciphertext.hex(), iv.hex())

    @staticmethod
    def decrypt_3des_cbc(ciphertext_hex: str, iv_hex: str, key: bytes) -> str:
        """Decrypt using TripleDES in CBC mode (for legacy/comparison only!)"""
        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
            iv = bytes.fromhex(iv_hex)
            
            decryptor = Cipher(
                algorithms.TripleDES(key),
                modes.CBC(iv),
                backend=default_backend()
            ).decryptor()
            
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(64).unpadder()
            plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext_bytes.decode('utf-8')
        except Exception as e:
            raise DecryptionError(f"3DES Decryption failed: {str(e)}") from e

    @staticmethod
    def generate_rsa_key_pair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    @staticmethod
    def encrypt_private_key(private_key_pem: bytes, master_key: bytes) -> Tuple[str, str, str]:
        return CryptoVault.encrypt_aes_gcm(private_key_pem.decode('utf-8'), master_key)

    @staticmethod
    def decrypt_private_key(encrypted_private_key_hex: str, iv_hex: str, auth_tag_hex: str, master_key: bytes) -> bytes:
        private_key_pem_str = CryptoVault.decrypt_aes_gcm(encrypted_private_key_hex, iv_hex, auth_tag_hex, master_key)
        return private_key_pem_str.encode('utf-8')

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(CryptoVault.SALT_SIZE)

