
import os
import sys
import pyodbc
import unittest
from dotenv import load_dotenv
from core.crypto_vault import CryptoVault, IntegrityError, DecryptionError
from services.fortress_vault_service import FortressVaultService
from config.sql_server_config import get_sql_server_connection

# Load environment variables
load_dotenv()


class TestFortressVaultSecurity(unittest.TestCase):
    test_db_suffix = "_Test"
    test_db_name = None
    original_db_name = None

    @classmethod
    def setUpClass(cls):
        """
        Chạy trước tất cả test case: Tạo database test
        """
        print("\n" + "=" * 60)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 60)

        cls.original_db_name = os.getenv("SQL_DATABASE")
        cls.test_db_name = cls.original_db_name + cls.test_db_suffix

        # Step 1: Create test database
        print(f"Creating test database: {cls.test_db_name}")
        conn = cls._get_master_connection()
        cursor = conn.cursor()
        try:
            # Drop test database if exists
            cursor.execute(f"IF EXISTS (SELECT name FROM sys.databases WHERE name = '{cls.test_db_name}') DROP DATABASE {cls.test_db_name};")
            conn.commit()

            # Create test database
            cursor.execute(f"CREATE DATABASE {cls.test_db_name};")
            conn.commit()
            print("✓ Test database created successfully")
        finally:
            cursor.close()
            conn.close()

        # Step 2: Update environment to use test database
        os.environ["SQL_DATABASE"] = cls.test_db_name

        # Step 3: Initialize test database schema
        print("Initializing test database schema...")
        cls._init_test_database_schema()
        print("✓ Test database schema initialized")
        print("=" * 60)

    @classmethod
    def tearDownClass(cls):
        """
        Chạy sau tất cả test case: Xóa database test
        """
        print("\n" + "=" * 60)
        print("CLEANING UP TEST ENVIRONMENT")
        print("=" * 60)
        print(f"Deleting test database: {cls.test_db_name}")

        conn = cls._get_master_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"ALTER DATABASE {cls.test_db_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE;")
            cursor.execute(f"DROP DATABASE {cls.test_db_name};")
            conn.commit()
            print("✓ Test database deleted successfully")
        finally:
            cursor.close()
            conn.close()

        # Restore original database name
        os.environ["SQL_DATABASE"] = cls.original_db_name
        print("=" * 60)

    @classmethod
    def _get_master_connection(cls):
        """Helper: Kết nối đến master database để tạo/xóa test database"""
        server = os.getenv("SQL_SERVER", "localhost")
        username = os.getenv("SQL_USERNAME", "sa")
        password = os.getenv("SQL_PASSWORD", "")
        driver = os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}")

        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE=master;"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str)

    @classmethod
    def _init_test_database_schema(cls):
        """Helper: Tạo schema và dữ liệu ban đầu cho test database"""
        conn = get_sql_server_connection()
        cursor = conn.cursor()
        try:
            # Create tables (simplified schema for testing)
            cursor.execute("""
                CREATE TABLE roles (
                    role_id INT IDENTITY(1,1) PRIMARY KEY,
                    role_name NVARCHAR(50) NOT NULL UNIQUE
                );

                CREATE TABLE users (
                    user_id INT IDENTITY(1,1) PRIMARY KEY,
                    username NVARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARBINARY(256) NOT NULL,
                    role_id INT NOT NULL FOREIGN KEY REFERENCES roles(role_id),
                    is_active BIT DEFAULT 1
                );

                CREATE TABLE user_security_profiles (
                    profile_id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id) UNIQUE,
                    salt VARBINARY(256) NOT NULL,
                    key_derivation_iterations INT NOT NULL
                );

                CREATE TABLE categories (
                    category_id INT IDENTITY(1,1) PRIMARY KEY,
                    category_name NVARCHAR(100) NOT NULL UNIQUE
                );

                CREATE TABLE cipher_configs (
                    cipher_config_id INT IDENTITY(1,1) PRIMARY KEY,
                    algorithm_name NVARCHAR(50) NOT NULL,
                    key_size INT NOT NULL,
                    mode NVARCHAR(50) NOT NULL
                );

                CREATE TABLE vault_credentials (
                    vault_credential_id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id INT NOT NULL FOREIGN KEY REFERENCES users(user_id),
                    category_id INT NULL,
                    item_name NVARCHAR(255) NOT NULL,
                    encrypted_data NVARCHAR(MAX) NOT NULL,
                    iv NVARCHAR(255) NOT NULL,
                    auth_tag NVARCHAR(255) NOT NULL,
                    cipher_config_id INT NOT NULL
                );

                CREATE TABLE log_actions (
                    action_id INT PRIMARY KEY,
                    action_name NVARCHAR(100) NOT NULL UNIQUE
                );

                CREATE TABLE audit_logs (
                    audit_log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    action_id INT NOT NULL,
                    user_id INT NULL,
                    ip_address NVARCHAR(50) NULL,
                    device_info NVARCHAR(255) NULL,
                    action_details NVARCHAR(MAX) NULL,
                    created_at DATETIME DEFAULT GETDATE()
                );
            """)
            conn.commit()

            # Insert initial data
            cursor.execute("""
                INSERT INTO roles (role_name) VALUES (N'User'), (N'Admin'), (N'Auditor');
                INSERT INTO categories (category_name) VALUES (N'Other');
                INSERT INTO cipher_configs (algorithm_name, key_size, mode) VALUES (N'AES-GCM', 256, N'GCM');
                INSERT INTO log_actions (action_id, action_name) VALUES
                    (1, N'Register'), (2, N'Login Success'), (3, N'Login Failed'),
                    (4, N'Add Vault Item'), (5, N'View Vault Item Success'), (6, N'View Vault Item Failed');
            """)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def setUp(self):
        """Chạy trước mỗi test case: Khởi tạo service và dữ liệu test"""
        self.service = FortressVaultService()
        self.test_user_password = "UserTest123!"
        self.test_admin_password = "AdminTest123!"
        self.test_auditor_password = "AuditorTest123!"
        self.test_plaintext_data = "Số CCCD nhạy cảm: 0123456789"

    def test_case_1_user_create_and_store_data(self):
        """
        Test case 1: Tạo tài khoản User, lưu dữ liệu nhạy cảm, chứng minh dữ liệu mã hóa (không rõ)
        """
        print("\n" + "-" * 60)
        print("TEST CASE 1: User tạo và lưu dữ liệu nhạy cảm")
        print("-" * 60)

        try:
            # Step 1: Register user
            self.user_id = self.service.register_user(
                username="test_user_1",
                password=self.test_user_password,
                role_name="User",
                ip_address="192.168.1.10",
                device_info="Test Device 1"
            )
            print(f"✓ Đăng ký User thành công (User ID: {self.user_id})")

            # Step 2: Login user
            self.user_session = self.service.login_user(
                username="test_user_1",
                password=self.test_user_password,
                ip_address="192.168.1.10",
                device_info="Test Device 1"
            )
            print(f"✓ Đăng nhập User thành công")

            # Step 3: Add vault item (sensitive data)
            self.vault_item_id = self.service.add_vault_item(
                user_id=self.user_session["user_id"],
                role_name=self.user_session["role_name"],
                master_password=self.test_user_password,
                user_salt=self.user_session["user_salt"],
                item_name="CCCD của tôi",
                item_username="N/A",
                item_password=self.test_plaintext_data,
                item_url="N/A",
                item_notes="Thông tin CCCD cá nhân",
                ip_address="192.168.1.10",
                device_info="Test Device 1"
            )
            print(f"✓ Lưu dữ liệu vào Vault thành công (Vault Item ID: {self.vault_item_id})")

            # Step 4: Retrieve ciphertext from DB and show it's encrypted (not plaintext)
            conn = get_sql_server_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_data FROM vault_credentials WHERE vault_credential_id = ?;", (self.vault_item_id,))
            ciphertext = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            print(f"✓ Dữ liệu trong DB (Ciphertext - đã mã hóa): {ciphertext[:100]}...")
            self.assertNotIn(self.test_plaintext_data, ciphertext, "Dữ liệu trong DB không được ở dạng rõ!")
            print("✓ PASS: Dữ liệu trong DB được mã hóa (không ở dạng rõ)")

        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")

    def test_case_2_user_view_own_data_success(self):
        """
        Test case 2: User đăng nhập và xem dữ liệu thành công
        """
        print("\n" + "-" * 60)
        print("TEST CASE 2: User xem dữ liệu của mình thành công")
        print("-" * 60)

        try:
            vault_item = self.service.view_vault_item(
                user_id=self.user_session["user_id"],
                role_name=self.user_session["role_name"],
                vault_item_id=self.vault_item_id,
                master_password=self.test_user_password,
                user_salt=self.user_session["user_salt"],
                ip_address="192.168.1.10",
                device_info="Test Device 1"
            )
            decrypted_data = vault_item["decrypted_data"]["Password"]
            print(f"✓ Dữ liệu giải mã thành công: {decrypted_data}")
            self.assertEqual(decrypted_data, self.test_plaintext_data, "Dữ liệu giải mã không khớp với dữ liệu ban đầu!")
            print("✓ PASS: User xem dữ liệu của mình thành công (giải mã đúng)")

        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")

    def test_case_3_admin_cannot_view_user_data(self):
        """
        Test case 3: Admin không thể xem dữ liệu của User
        """
        print("\n" + "-" * 60)
        print("TEST CASE 3: Admin không thể xem dữ liệu của User")
        print("-" * 60)

        try:
            # Register and login Admin
            admin_id = self.service.register_user(
                username="test_admin_1",
                password=self.test_admin_password,
                role_name="Admin",
                ip_address="192.168.1.1",
                device_info="Admin Test Device"
            )
            admin_session = self.service.login_user(
                username="test_admin_1",
                password=self.test_admin_password,
                ip_address="192.168.1.1",
                device_info="Admin Test Device"
            )
            print(f"✓ Đăng ký/Đăng nhập Admin thành công")

            # Admin tries to view user's data - should fail
            with self.assertRaises(PermissionError) as context:
                self.service.view_vault_item(
                    user_id=admin_session["user_id"],
                    role_name=admin_session["role_name"],
                    vault_item_id=self.vault_item_id,
                    master_password=self.test_admin_password,
                    user_salt=self.user_session["user_salt"],
                    ip_address="192.168.1.1",
                    device_info="Admin Test Device"
                )

            print(f"✓ Hệ thống đã chặn Admin xem dữ liệu User: {str(context.exception)}")
            print("✓ PASS: Admin không thể xem dữ liệu của User")

        except AssertionError:
            self.fail("✗ FAIL: Admin đã xem được dữ liệu User (điều này không được phép!)")
        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")

    def test_case_4_auditor_can_view_logs_not_vault(self):
        """
        Test case 4: Auditor xem Audit Log được, nhưng không xem được Vault
        """
        print("\n" + "-" * 60)
        print("TEST CASE 4: Auditor xem Audit Log, không xem được Vault")
        print("-" * 60)

        try:
            # Register and login Auditor
            auditor_id = self.service.register_user(
                username="test_auditor_1",
                password=self.test_auditor_password,
                role_name="Auditor",
                ip_address="192.168.1.20",
                device_info="Auditor Test Device"
            )
            auditor_session = self.service.login_user(
                username="test_auditor_1",
                password=self.test_auditor_password,
                ip_address="192.168.1.20",
                device_info="Auditor Test Device"
            )
            print(f"✓ Đăng ký/Đăng nhập Auditor thành công")

            # Step 1: Auditor views audit logs - should work
            audit_logs = self.service.auditor_view_logs(
                user_id=auditor_session["user_id"],
                role_name=auditor_session["role_name"],
                page_number=1,
                page_size=20
            )
            print(f"✓ Auditor xem được {len(audit_logs)} bản ghi Audit Log")
            self.assertGreater(len(audit_logs), 0, "Auditor phải xem được ít nhất 1 bản ghi log!")

            # Step 2: Auditor tries to view vault item - should fail
            with self.assertRaises(PermissionError) as context:
                self.service.view_vault_item(
                    user_id=auditor_session["user_id"],
                    role_name=auditor_session["role_name"],
                    vault_item_id=self.vault_item_id,
                    master_password=self.test_auditor_password,
                    user_salt=self.user_session["user_salt"],
                    ip_address="192.168.1.20",
                    device_info="Auditor Test Device"
                )

            print(f"✓ Hệ thống đã chặn Auditor xem Vault: {str(context.exception)}")
            print("✓ PASS: Auditor chỉ xem được Audit Log, không xem được Vault")

        except AssertionError as e:
            self.fail(f"✗ FAIL: {str(e)}")
        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")

    def test_case_5_tampered_ciphertext_detected(self):
        """
        Test case 5: Thay đổi Ciphertext, AES-GCM phát hiện và từ chối giải mã
        """
        print("\n" + "-" * 60)
        print("TEST CASE 5: Thay đổi Ciphertext, AES-GCM phát hiện")
        print("-" * 60)

        try:
            # Step 1: Tamper with ciphertext in DB
            conn = get_sql_server_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_data FROM vault_credentials WHERE vault_credential_id = ?;", (self.vault_item_id,))
            original_ciphertext = cursor.fetchone()[0]

            # Tamper with it: change first character
            tampered_ciphertext = list(original_ciphertext)
            tampered_ciphertext[0] = '0' if tampered_ciphertext[0] != '0' else '1'
            tampered_ciphertext = "".join(tampered_ciphertext)

            cursor.execute("UPDATE vault_credentials SET encrypted_data = ? WHERE vault_credential_id = ?;", (tampered_ciphertext, self.vault_item_id))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✓ Đã thay đổi Ciphertext trong DB")

            # Step 2: Try to decrypt - should raise IntegrityError
            with self.assertRaises((IntegrityError, DecryptionError)) as context:
                self.service.view_vault_item(
                    user_id=self.user_session["user_id"],
                    role_name=self.user_session["role_name"],
                    vault_item_id=self.vault_item_id,
                    master_password=self.test_user_password,
                    user_salt=self.user_session["user_salt"],
                    ip_address="192.168.1.10",
                    device_info="Test Device 1"
                )

            print(f"✓ AES-GCM đã phát hiện dữ liệu bị thay đổi: {str(context.exception)}")
            print("✓ PASS: Dữ liệu bị thay đổi được phát hiện (Integrity Check)")

        except AssertionError:
            self.fail("✗ FAIL: Hệ thống không phát hiện dữ liệu bị thay đổi!")
        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")

    def test_case_6_audit_logs_complete(self):
        """
        Test case 6: Kiểm tra audit_logs có đầy đủ các hành động không
        """
        print("\n" + "-" * 60)
        print("TEST CASE 6: Kiểm tra Audit Log đầy đủ")
        print("-" * 60)

        try:
            # Get all audit logs from DB
            conn = get_sql_server_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT action_id, action_details FROM audit_logs ORDER BY audit_log_id;")
            logs = cursor.fetchall()
            cursor.close()
            conn.close()

            print(f"✓ Tìm thấy {len(logs)} bản ghi trong audit_logs:")
            for log in logs:
                print(f"  - Action ID: {log[0]}, Details: {log[1][:80]}...")

            # Verify key actions are present
            action_ids_found = [log[0] for log in logs]
            required_action_ids = [1, 2, 4, 5, 3, 6]  # Register, Login Success, Add Vault, View Vault, etc.

            for action_id in required_action_ids:
                if action_id == 3:  # Login Failed may or may not be present, skip for now
                    continue
                self.assertIn(action_id, action_ids_found, f"Thiếu hành động với action_id {action_id} trong audit_logs!")

            print("✓ PASS: Audit Log ghi nhận đầy đủ các hành động")
            print("-" * 60)

        except Exception as e:
            self.fail(f"✗ FAIL: {str(e)}")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=0)

