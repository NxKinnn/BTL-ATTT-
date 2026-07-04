
from config.database import execute_query, execute_non_query
from services.auth_service import AuthService

print("=== Setting up initial data ===")

# 1. Add categories
print("\n1. Adding categories...")
categories = [
    ("Email", "Email account credentials"),
    ("Social Media", "Social media credentials"),
    ("Finance", "Financial and banking credentials"),
    ("Other", "Other types of credentials")
]

for name, desc in categories:
    existing = execute_query("SELECT category_id FROM categories WHERE category_name = ?", (name,))
    if not existing:
        execute_non_query(
            "INSERT INTO categories (category_name, description) VALUES (?, ?)",
            (name, desc)
        )
        print(f"   Added category: {name}")
    else:
        print(f"   Category already exists: {name}")

# 2. Create default admin and auditor users
print("\n2. Creating default users...")
default_users = [
    {"username": "admin", "password": "Admin123!", "role": "Admin"},
    {"username": "auditor", "password": "Audit123!", "role": "Auditor"}
]

for user_data in default_users:
    existing = execute_query("SELECT user_id FROM users WHERE username = ?", (user_data["username"],))
    if not existing:
        user_id = AuthService.register_user(
            username=user_data["username"],
            password=user_data["password"],
            role_name=user_data["role"]
        )
        if user_id:
            print(f"   Created {user_data['role']}: {user_data['username']} (password: {user_data['password']})")
        else:
            print(f"   Failed to create {user_data['role']}: {user_data['username']}")
    else:
        print(f"   User already exists: {user_data['username']}")

print("\n=== Initial data setup complete! ===")

