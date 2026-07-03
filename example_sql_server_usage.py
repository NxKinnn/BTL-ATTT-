
from services.fortress_vault_service import FortressVaultService


def main():
    print("=== FortressVault SQL Server Backend Example ===\n")
    service = FortressVaultService()

    # --- 1. Register Users ---
    print("1. Registering users...")
    try:
        # Register a User
        user_id = service.register_user(
            username="john_doe",
            password="StrongPassword123!",
            role_name="User",
            ip_address="192.168.1.100",
            device_info="Windows 11 - Chrome"
        )
        print(f"   - User 'john_doe' registered with ID: {user_id}")

        # Register an Admin
        admin_id = service.register_user(
            username="admin_user",
            password="AdminStrongPassword123!",
            role_name="Admin",
            ip_address="192.168.1.1",
            device_info="Windows Server 2022 - Edge"
        )
        print(f"   - Admin 'admin_user' registered with ID: {admin_id}")

        # Register an Auditor
        auditor_id = service.register_user(
            username="auditor_user",
            password="AuditorStrongPassword123!",
            role_name="Auditor",
            ip_address="192.168.1.200",
            device_info="macOS Sonoma - Safari"
        )
        print(f"   - Auditor 'auditor_user' registered with ID: {auditor_id}")
    except Exception as e:
        print(f"   - Registration error: {e}")
    print()

    # --- 2. Login as User ---
    print("2. Logging in as 'john_doe'...")
    try:
        user_session = service.login_user(
            username="john_doe",
            password="StrongPassword123!",
            ip_address="192.168.1.100",
            device_info="Windows 11 - Chrome"
        )
        print(f"   - Logged in successfully!")
        print(f"   - User ID: {user_session['user_id']}")
        print(f"   - Role: {user_session['role_name']}")
    except Exception as e:
        print(f"   - Login error: {e}")
    print()

    # --- 3. Add Vault Item ---
    print("3. Adding a vault item for 'john_doe'...")
    try:
        vault_item_id = service.add_vault_item(
            user_id=user_session["user_id"],
            role_name=user_session["role_name"],
            master_password="StrongPassword123!",  # Same as login password
            user_salt=user_session["user_salt"],
            item_name="Gmail Account",
            item_username="john.doe@gmail.com",
            item_password="GmailPassword123!",
            item_url="https://mail.google.com",
            item_notes="My personal Gmail account",
            ip_address="192.168.1.100",
            device_info="Windows 11 - Chrome"
        )
        print(f"   - Vault item added with ID: {vault_item_id}")
    except Exception as e:
        print(f"   - Add vault item error: {e}")
    print()

    # --- 4. View Vault Item ---
    print("4. Viewing vault item for 'john_doe'...")
    try:
        vault_item = service.view_vault_item(
            user_id=user_session["user_id"],
            role_name=user_session["role_name"],
            vault_item_id=vault_item_id,
            master_password="StrongPassword123!",
            user_salt=user_session["user_salt"],
            ip_address="192.168.1.100",
            device_info="Windows 11 - Chrome"
        )
        print(f"   - Successfully viewed vault item!")
        print(f"   - Item Name: {vault_item['item_name']}")
        print(f"   - Decrypted Data: {vault_item['decrypted_data']}")
    except Exception as e:
        print(f"   - View vault item error: {e}")
    print()

    # --- 5. Login as Admin and try to view vault item (should fail!) ---
    print("5. Logging in as 'admin_user' and trying to view vault item...")
    try:
        admin_session = service.login_user(
            username="admin_user",
            password="AdminStrongPassword123!",
            ip_address="192.168.1.1",
            device_info="Windows Server 2022 - Edge"
        )
        print(f"   - Admin logged in successfully!")

        # Admin tries to view user's vault item - should fail!
        try:
            service.view_vault_item(
                user_id=admin_session["user_id"],
                role_name=admin_session["role_name"],
                vault_item_id=vault_item_id,
                master_password="AdminStrongPassword123!",
                user_salt=user_session["user_salt"],  # Even if admin had salt, role check fails!
                ip_address="192.168.1.1",
                device_info="Windows Server 2022 - Edge"
            )
            print("   - ERROR: Admin was able to view vault item (this should NOT happen!)")
        except PermissionError as e:
            print(f"   - SUCCESS: Admin cannot view vault item! Error: {e}")
    except Exception as e:
        print(f"   - Admin login error: {e}")
    print()

    # --- 6. Login as Auditor and view audit logs ---
    print("6. Logging in as 'auditor_user' and viewing audit logs...")
    try:
        auditor_session = service.login_user(
            username="auditor_user",
            password="AuditorStrongPassword123!",
            ip_address="192.168.1.200",
            device_info="macOS Sonoma - Safari"
        )
        print(f"   - Auditor logged in successfully!")

        audit_logs = service.auditor_view_logs(
            user_id=auditor_session["user_id"],
            role_name=auditor_session["role_name"],
            page_number=1,
            page_size=10
        )
        print(f"   - Found {len(audit_logs)} audit logs!")
        print("   - Recent logs:")
        for log in audit_logs[:3]:  # Show first 3 logs
            print(f"     - [{log['created_at']}] {log['action_name']}: {log['action_details']}")
    except Exception as e:
        print(f"   - Auditor error: {e}")


if __name__ == "__main__":
    main()

