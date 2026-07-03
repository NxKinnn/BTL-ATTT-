
import os
from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError


def main():
    print("=== Secure Personal Data Vault Example ===")
    print()

    # 1. User enters Master Password and generates Salt
    master_password = "MyStrongMasterPassword123!"
    salt = os.urandom(16)  # Store this salt in DB (not the key!)
    print(f"Master Password: {master_password}")
    print(f"Salt (hex): {salt.hex()}")
    print()

    # 2. Generate Master Key using PBKDF2 (not stored in DB, only in RAM)
    print("Generating Master Key using PBKDF2...")
    aes_key = CryptoVault.derive_master_key(master_password, salt, key_length=32)
    des3_key = CryptoVault.derive_master_key(master_password, salt, key_length=24)
    print(f"AES-256 Master Key (hex): {aes_key.hex()}")
    print()

    # 3. Encrypt data using AES-GCM
    plaintext = "Phone: 0123456789, Email: example@email.com, ID: 123456789"
    print(f"Plaintext: {plaintext}")
    ciphertext_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_aes_gcm(plaintext, aes_key)
    print(f"Ciphertext (hex): {ciphertext_hex}")
    print(f"IV (hex): {iv_hex}")
    print(f"Auth Tag (hex): {auth_tag_hex}")
    print()

    # 4. Decrypt data using AES-GCM
    print("Decrypting data using AES-GCM...")
    try:
        decrypted = CryptoVault.decrypt_aes_gcm(ciphertext_hex, iv_hex, auth_tag_hex, aes_key)
        print(f"Decrypted Plaintext: {decrypted}")
    except IntegrityError:
        print("Error: Data tampered or wrong key!")
    except DecryptionError as e:
        print(f"Decryption error: {e}")
    print()

    # 5. Check data integrity (modify ciphertext)
    print("=== Checking Data Integrity ===")
    tampered_ciphertext = list(ciphertext_hex)
    tampered_ciphertext[0] = '0'
    tampered_ciphertext_hex = ''.join(tampered_ciphertext)
    print(f"Tampered Ciphertext (hex): {tampered_ciphertext_hex}")
    try:
        CryptoVault.decrypt_aes_gcm(tampered_ciphertext_hex, iv_hex, auth_tag_hex, aes_key)
    except IntegrityError as e:
        print(f"Detected integrity error: {e}")
    print()

    # 6. Encrypt/Decrypt using TripleDES (legacy/comparison)
    print("=== TripleDES Encryption/Decryption ===")
    ciphertext_3des_hex, iv_3des_hex = CryptoVault.encrypt_3des(plaintext, des3_key)
    print(f"3DES Ciphertext (hex): {ciphertext_3des_hex}")
    decrypted_3des = CryptoVault.decrypt_3des(ciphertext_3des_hex, iv_3des_hex, des3_key)
    print(f"Decrypted 3DES Plaintext: {decrypted_3des}")


if __name__ == "__main__":
    main()

