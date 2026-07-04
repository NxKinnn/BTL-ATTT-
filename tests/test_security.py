
"""
FortressVault Security Tests
Tests for AES-256-GCM, TripleDES, PBKDF2, etc.
"""
import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError


@pytest.fixture
def test_master_password():
    return "MyStrongMasterPassword123!"


@pytest.fixture
def test_salt():
    return os.urandom(16)


def test_pbkdf2_key_derivation(test_master_password, test_salt):
    """Kiểm tra PBKDF2 tạo khóa đúng độ dài"""
    aes_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=32)
    assert len(aes_key) == 32

    des3_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=24)
    assert len(des3_key) == 24


def test_aes_gcm_encrypt_decrypt(test_master_password, test_salt):
    """Kiểm tra AES-GCM mã hóa và giải mã đúng"""
    aes_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=32)
    plaintext = "Đây là dữ liệu cá nhân nhạy cảm: 0123456789"
    ciphertext_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_aes_gcm(plaintext, aes_key)
    decrypted = CryptoVault.decrypt_aes_gcm(ciphertext_hex, iv_hex, auth_tag_hex, aes_key)
    assert decrypted == plaintext


def test_aes_gcm_integrity_check(test_master_password, test_salt):
    """Kiểm tra AES-GCM phát hiện dữ liệu bị chỉnh sửa"""
    aes_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=32)
    plaintext = "Đây là dữ liệu cá nhân nhạy cảm: 0123456789"
    ciphertext_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_aes_gcm(plaintext, aes_key)

    # Thay đổi một ký tự trong ciphertext
    tampered_ciphertext = list(ciphertext_hex)
    if tampered_ciphertext:
        tampered_ciphertext[0] = '0' if tampered_ciphertext[0] != '0' else '1'
    tampered_ciphertext_hex = ''.join(tampered_ciphertext)

    # Kiểm tra có raise IntegrityError hoặc DecryptionError
    try:
        CryptoVault.decrypt_aes_gcm(tampered_ciphertext_hex, iv_hex, auth_tag_hex, aes_key)
        assert False, "Should raise an error!"
    except (IntegrityError, DecryptionError):
        assert True


def test_3des_encrypt_decrypt(test_master_password, test_salt):
    """Kiểm tra 3DES mã hóa và giải mã đúng"""
    des3_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=24)
    plaintext = "Đây là dữ liệu cá nhân nhạy cảm: 0123456789"
    ciphertext_hex, iv_hex = CryptoVault.encrypt_3des_cbc(plaintext, des3_key)
    decrypted = CryptoVault.decrypt_3des_cbc(ciphertext_hex, iv_hex, des3_key)
    assert decrypted == plaintext


def test_aes_gcm_wrong_key(test_master_password, test_salt):
    """Kiểm tra AES-GCM giải mã với khóa sai"""
    aes_key = CryptoVault.derive_master_key(test_master_password, test_salt, key_size=32)
    wrong_aes_key = CryptoVault.derive_master_key("WrongPassword123!", test_salt, key_size=32)
    plaintext = "Đây là dữ liệu cá nhân nhạy cảm: 0123456789"
    ciphertext_hex, iv_hex, auth_tag_hex = CryptoVault.encrypt_aes_gcm(plaintext, aes_key)

    try:
        CryptoVault.decrypt_aes_gcm(ciphertext_hex, iv_hex, auth_tag_hex, wrong_aes_key)
        assert False, "Should raise an error!"
    except (IntegrityError, DecryptionError):
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

