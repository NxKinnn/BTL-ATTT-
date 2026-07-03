
import customtkinter as ctk
from tkinter import ttk, messagebox
from config.database import init_db
from services.auth_service import AuthService
from services.vault_service import VaultService
from services.audit_service import AuditService
from core.crypto_vault import CryptoVault


class FortressVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FortressVault - Secure Personal Data Vault")
        self.root.geometry("1200x800")

        # Set appearance mode and default color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Current user data
        self.current_user = None
        self.master_key = None  # Store derived key instead of plaintext password
        self.user_salt = None

        # Initialize database
        try:
            init_db()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            self.root.destroy()
            return

        # Show login/register screen
        self.show_auth_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_auth_screen(self):
        self.clear_screen()

        self.auth_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.auth_frame.pack(pady=50, padx=50, fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(
            self.auth_frame,
            text="🔐 FortressVault",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(30, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.auth_frame,
            text="Secure Personal Data Vault",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.pack(pady=(0, 30))

        # Tabs for login/register
        self.auth_tabview = ctk.CTkTabview(self.auth_frame)
        self.auth_tabview.pack(pady=20, padx=60, fill="both", expand=True)

        self.tab_login = self.auth_tabview.add("Login")
        self.tab_register = self.auth_tabview.add("Register")

        # Login tab
        self.setup_login_tab()

        # Register tab
        self.setup_register_tab()

    def setup_login_tab(self):
        self.lbl_login_username = ctk.CTkLabel(self.tab_login, text="Username:")
        self.lbl_login_username.pack(pady=(20, 5))
        self.entry_login_username = ctk.CTkEntry(self.tab_login, placeholder_text="Enter username")
        self.entry_login_username.pack(pady=5, padx=20, fill="x")

        self.lbl_login_password = ctk.CTkLabel(self.tab_login, text="Password:")
        self.lbl_login_password.pack(pady=(10, 5))
        self.entry_login_password = ctk.CTkEntry(self.tab_login, placeholder_text="Enter password", show="*")
        self.entry_login_password.pack(pady=5, padx=20, fill="x")

        self.btn_login = ctk.CTkButton(
            self.tab_login,
            text="Login",
            command=self.handle_login,
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.btn_login.pack(pady=30)

    def setup_register_tab(self):
        self.lbl_reg_username = ctk.CTkLabel(self.tab_register, text="Username:")
        self.lbl_reg_username.pack(pady=(20, 5))
        self.entry_reg_username = ctk.CTkEntry(self.tab_register, placeholder_text="Enter username")
        self.entry_reg_username.pack(pady=5, padx=20, fill="x")

        self.lbl_reg_password = ctk.CTkLabel(self.tab_register, text="Password:")
        self.lbl_reg_password.pack(pady=(10, 5))
        self.entry_reg_password = ctk.CTkEntry(self.tab_register, placeholder_text="Enter password", show="*")
        self.entry_reg_password.pack(pady=5, padx=20, fill="x")

        self.lbl_reg_confirm_password = ctk.CTkLabel(self.tab_register, text="Confirm Password:")
        self.lbl_reg_confirm_password.pack(pady=(10, 5))
        self.entry_reg_confirm_password = ctk.CTkEntry(self.tab_register, placeholder_text="Confirm password", show="*")
        self.entry_reg_confirm_password.pack(pady=5, padx=20, fill="x")

        self.btn_register = ctk.CTkButton(
            self.tab_register,
            text="Register",
            command=self.handle_register,
            font=ctk.CTkFont(weight="bold"),
            height=40
        )
        self.btn_register.pack(pady=30)

    def handle_login(self):
        username = self.entry_login_username.get().strip()
        password = self.entry_login_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        user = AuthService.login_user(username, password, "127.0.0.1", "CustomTkinter App")
        if user:
            self.current_user = user
            self.user_salt = user['salt']
            # Derive master key from password and salt
            self.master_key = CryptoVault.derive_master_key(password, self.user_salt)
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    def handle_register(self):
        username = self.entry_reg_username.get().strip()
        password = self.entry_reg_password.get().strip()
        confirm_password = self.entry_reg_confirm_password.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        user_id = AuthService.register_user(username, password, "User", "127.0.0.1", "CustomTkinter App")
        if user_id:
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.auth_tabview.set("Login")
        else:
            messagebox.showerror("Error", "Username already exists or registration failed!")

    def show_dashboard(self):
        self.clear_screen()

        # Main window layout with sidebar
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Sidebar widgets
        self.lbl_user = ctk.CTkLabel(
            self.sidebar,
            text=f"Welcome, {self.current_user['username']}",
            font=ctk.CTkFont(weight="bold")
        )
        self.lbl_user.pack(pady=20, padx=10)

        self.btn_vault = ctk.CTkButton(
            self.sidebar,
            text="🔑 My Vault",
            command=self.show_vault,
            width=180,
            height=40
        )
        self.btn_vault.pack(pady=10, padx=10)

        self.btn_audit = ctk.CTkButton(
            self.sidebar,
            text="📋 Audit Log",
            command=self.show_audit_log,
            width=180,
            height=40
        )
        self.btn_audit.pack(pady=10, padx=10)

        self.btn_logout = ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            command=self.logout,
            fg_color="#d9534f",
            hover_color="#c9302c",
            width=180,
            height=40
        )
        self.btn_logout.pack(pady=(40, 10), padx=10)

        # Show initial screen
        if self.current_user['role_name'] == 'User':
            self.show_vault()
        elif self.current_user['role_name'] == 'Auditor':
            self.show_audit_log()
        else:
            messagebox.showinfo("Admin", "Admin dashboard coming soon!")
            self.show_audit_log()

    def show_vault(self):
        self.clear_content_frame()

        # Vault title
        self.lbl_vault_title = ctk.CTkLabel(
            self.content_frame,
            text="🔑 My Vault",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_vault_title.pack(pady=20)

        # Button to add new item
        self.btn_add_vault = ctk.CTkButton(
            self.content_frame,
            text="➕ Add New Item",
            command=self.show_add_vault_dialog,
            fg_color="#5cb85c",
            hover_color="#4cae4c",
            height=40
        )
        self.btn_add_vault.pack(pady=10, padx=20, anchor="w")

        # Treeview to display vault items
        self.tree_frame = ctk.CTkFrame(self.content_frame)
        self.tree_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.vault_tree = ttk.Treeview(
            self.tree_frame,
            columns=("ID", "Name", "Category", "Created"),
            show="headings",
            height=15
        )
        self.vault_tree.heading("ID", text="ID")
        self.vault_tree.heading("Name", text="Item Name")
        self.vault_tree.heading("Category", text="Category")
        self.vault_tree.heading("Created", text="Created At")
        self.vault_tree.column("ID", width=50, anchor="center")
        self.vault_tree.column("Name", width=200)
        self.vault_tree.column("Category", width=150)
        self.vault_tree.column("Created", width=200, anchor="center")

        self.vault_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.vault_tree.yview)
        self.vault_tree.configure(yscrollcommand=self.vault_scrollbar.set)

        self.vault_tree.pack(side="left", fill="both", expand=True)
        self.vault_scrollbar.pack(side="right", fill="y")

        self.vault_tree.bind("<Double-1>", self.show_vault_item_details)

        self.load_vault_items()

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def load_vault_items(self):
        # Clear existing items
        for item in self.vault_tree.get_children():
            self.vault_tree.delete(item)

        # Get items from service
        items = VaultService.get_user_vault_items(
            self.current_user['user_id'],
            self.current_user['role_name']
        )

        # Insert into treeview
        for item in items:
            self.vault_tree.insert(
                "",
                "end",
                values=(
                    item['vault_id'],
                    item['item_name'],
                    item['category_name'] or "Other",
                    item['created_at']
                )
            )

    def show_add_vault_dialog(self):
        self.add_vault_window = ctk.CTkToplevel(self.root)
        self.add_vault_window.title("Add New Vault Item")
        self.add_vault_window.geometry("500x500")
        self.add_vault_window.grab_set()

        ctk.CTkLabel(self.add_vault_window, text="Item Name:").pack(pady=(20, 5), padx=20)
        self.entry_add_name = ctk.CTkEntry(self.add_vault_window)
        self.entry_add_name.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.add_vault_window, text="Username:").pack(pady=(10, 5), padx=20)
        self.entry_add_username = ctk.CTkEntry(self.add_vault_window)
        self.entry_add_username.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.add_vault_window, text="Password:").pack(pady=(10, 5), padx=20)
        self.entry_add_password = ctk.CTkEntry(self.add_vault_window, show="*")
        self.entry_add_password.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.add_vault_window, text="Notes:").pack(pady=(10, 5), padx=20)
        self.entry_add_notes = ctk.CTkTextbox(self.add_vault_window, height=100)
        self.entry_add_notes.pack(pady=5, padx=20, fill="x")

        self.btn_save_vault = ctk.CTkButton(
            self.add_vault_window,
            text="Save",
            command=self.save_new_vault_item,
            fg_color="#5cb85c",
            hover_color="#4cae4c",
            height=40
        )
        self.btn_save_vault.pack(pady=20)

    def save_new_vault_item(self):
        name = self.entry_add_name.get().strip()
        username = self.entry_add_username.get().strip()
        password = self.entry_add_password.get().strip()
        notes = self.entry_add_notes.get("1.0", "end").strip()

        if not name or not password:
            messagebox.showerror("Error", "Please enter at least item name and password!")
            return

        vault_id = VaultService.add_vault_item(
            user_id=self.current_user['user_id'],
            item_name=name,
            username=username if username else None,
            password=password,
            notes=notes if notes else None,
            master_key=self.master_key,
            ip_address="127.0.0.1",
            user_agent="CustomTkinter App"
        )

        if vault_id:
            messagebox.showinfo("Success", "Vault item saved successfully!")
            self.add_vault_window.destroy()
            self.load_vault_items()
        else:
            messagebox.showerror("Error", "Failed to save vault item!")

    def show_vault_item_details(self, event):
        selected = self.vault_tree.selection()
        if not selected:
            return

        item_id = self.vault_tree.item(selected[0])['values'][0]

        # Decrypt item
        decrypted = VaultService.decrypt_vault_item(
            user_id=self.current_user['user_id'],
            role=self.current_user['role_name'],
            vault_id=item_id,
            master_key=self.master_key,
            ip_address="127.0.0.1",
            user_agent="CustomTkinter App"
        )

        if decrypted:
            self.vault_detail_window = ctk.CTkToplevel(self.root)
            self.vault_detail_window.title("Vault Item Details")
            self.vault_detail_window.geometry("500x450")
            self.vault_detail_window.grab_set()

            ctk.CTkLabel(self.vault_detail_window, text=f"Name: {decrypted['item_name']}", font=ctk.CTkFont(weight="bold")).pack(pady=(20,10), padx=20, anchor="w")
            
            ctk.CTkLabel(self.vault_detail_window, text="Username:").pack(pady=(10,5), padx=20, anchor="w")
            self.lbl_detail_username = ctk.CTkLabel(self.vault_detail_window, text=decrypted['username'] or "N/A", wraplength=400)
            self.lbl_detail_username.pack(pady=5, padx=20, anchor="w")
            
            ctk.CTkLabel(self.vault_detail_window, text="Password:").pack(pady=(10,5), padx=20, anchor="w")
            self.lbl_detail_password = ctk.CTkLabel(self.vault_detail_window, text="*" * len(decrypted['password']), wraplength=400)
            self.lbl_detail_password.pack(pady=5, padx=20, anchor="w")
            
            self.btn_show_password = ctk.CTkButton(self.vault_detail_window, text="👁️ Show Password", command=lambda: self.toggle_password(decrypted['password']))
            self.btn_show_password.pack(pady=10, padx=20, anchor="w")
            
            ctk.CTkLabel(self.vault_detail_window, text="Notes:").pack(pady=(10,5), padx=20, anchor="w")
            self.lbl_detail_notes = ctk.CTkLabel(self.vault_detail_window, text=decrypted['notes'] or "N/A", wraplength=400, justify="left")
            self.lbl_detail_notes.pack(pady=5, padx=20, anchor="w")
        else:
            messagebox.showerror("Error", "Failed to decrypt vault item!")

    def toggle_password(self, real_password):
        if self.lbl_detail_password.cget("text").startswith("*"):
            self.lbl_detail_password.configure(text=real_password)
            self.btn_show_password.configure(text="🙈 Hide Password")
        else:
            self.lbl_detail_password.configure(text="*" * len(real_password))
            self.btn_show_password.configure(text="👁️ Show Password")

    def show_audit_log(self):
        self.clear_content_frame()

        self.lbl_audit_title = ctk.CTkLabel(
            self.content_frame,
            text="📋 Audit Log",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_audit_title.pack(pady=20)

        self.audit_tree_frame = ctk.CTkFrame(self.content_frame)
        self.audit_tree_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.audit_tree = ttk.Treeview(
            self.audit_tree_frame,
            columns=("ID", "Action", "User", "Details", "Timestamp"),
            show="headings",
            height=15
        )
        self.audit_tree.heading("ID", text="ID")
        self.audit_tree.heading("Action", text="Action")
        self.audit_tree.heading("User", text="User")
        self.audit_tree.heading("Details", text="Details")
        self.audit_tree.heading("Timestamp", text="Timestamp")
        self.audit_tree.column("ID", width=80, anchor="center")
        self.audit_tree.column("Action", width=150)
        self.audit_tree.column("User", width=150)
        self.audit_tree.column("Details", width=300)
        self.audit_tree.column("Timestamp", width=200, anchor="center")

        self.audit_scrollbar = ttk.Scrollbar(self.audit_tree_frame, orient="vertical", command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=self.audit_scrollbar.set)

        self.audit_tree.pack(side="left", fill="both", expand=True)
        self.audit_scrollbar.pack(side="right", fill="y")

        self.load_audit_log()

    def load_audit_log(self):
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)

        logs = AuditService.get_logs(
            user_id=self.current_user['user_id'],
            role=self.current_user['role_name']
        )

        for log in logs:
            self.audit_tree.insert(
                "",
                "end",
                values=(
                    log['audit_id'],
                    log['action_name'],
                    log['user_id'] or "System",
                    log['action_details'],
                    log['created_at']
                )
            )

    def logout(self):
        if self.current_user:
            AuthService.logout_user(
                user_id=self.current_user['user_id'],
                username=self.current_user['username'],
                ip_address="127.0.0.1",
                user_agent="CustomTkinter App"
            )
        
        self.current_user = None
        self.master_key = None
        self.user_salt = None
        self.show_auth_screen()


if __name__ == "__main__":
    root = ctk.CTk()
    app = FortressVaultApp(root)
    root.mainloop()

