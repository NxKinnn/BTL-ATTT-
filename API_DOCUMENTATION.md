# FortressVault Backend API Documentation

## Overview

This is a REST API built with FastAPI for the FortressVault password manager application. The API provides endpoints for authentication, managing vault items, and viewing audit logs.

**Base URL**: `http://localhost:8000`

**API Documentation UI**: Visit `http://localhost:8000/docs` for interactive Swagger UI or `http://localhost:8000/redoc` for ReDoc.

---

## Authentication

All protected endpoints require a valid JWT (JSON Web Token) in the Authorization header.

### Authentication Flow:

1. Register an account or login to get an `access_token`.
2. Include the token in all subsequent requests: `Authorization: Bearer <access_token>`.

---

## Endpoints

### 1. Root

#### GET `/`

Returns a simple welcome message and links to documentation.

**Response**:
```json
{
  "message": "FortressVault API",
  "docs": "/docs"
}
```

---

### 2. Authentication Endpoints

#### POST `/api/auth/register`

Register a new user account.

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK)**:
```json
{
  "message": "Registration successful",
  "user_id": 1
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Username already exists or registration failed"
}
```

---

#### POST `/api/auth/login`

Login and get an access token. Uses OAuth2 password flow.

**Request (form-data)**:
```
username: "string"
password: "string"
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "role_name": "User"
  }
}
```

**Response (401 Unauthorized)**:
```json
{
  "detail": "Incorrect username or password"
}
```

---

#### POST `/api/auth/logout`

Logout (records audit log event).

**Authorization Header Required**: Yes

**Response (200 OK)**:
```json
{
  "message": "Logout successful"
}
```

---

### 3. Vault Endpoints

#### GET `/api/vault/items`

Get all vault items for the current user (encrypted, without sensitive data decrypted).

**Authorization Header Required**: Yes

**Response (200 OK)**:
```json
[
  {
    "vault_id": 1,
    "user_id": 1,
    "category_id": null,
    "item_name": "My Email",
    "encrypted_password": "hex_string",
    "iv": "hex_string",
    "auth_tag": "hex_string",
    "cipher_config_id": 1,
    "created_at": "2024-07-03T10:00:00",
    "updated_at": "2024-07-03T10:00:00",
    "category_name": null
  }
]
```

---

#### POST `/api/vault/items`

Add a new vault item.

**Authorization Header Required**: Yes

**Query Parameters**:
- `master_password`: (string, required) The user's master password to derive encryption key.

**Request Body**:
```json
{
  "item_name": "string",
  "username": "string (optional)",
  "password": "string",
  "notes": "string (optional)",
  "category_id": 1 (optional)
}
```

**Response (200 OK)**:
```json
{
  "message": "Vault item added successfully",
  "vault_id": 2
}
```

---

#### GET `/api/vault/items/{vault_id}`

Decrypt and get a specific vault item by ID.

**Authorization Header Required**: Yes

**Path Parameters**:
- `vault_id`: (integer, required) ID of the vault item.

**Query Parameters**:
- `master_password`: (string, required) The user's master password to derive decryption key.

**Response (200 OK)**:
```json
{
  "vault_id": 1,
  "item_name": "My Email",
  "username": "user@example.com",
  "password": "secret123",
  "notes": "My important notes"
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Vault item not found or decryption failed"
}
```

---

#### PUT `/api/vault/items/{vault_id}`

Update an existing vault item.

**Authorization Header Required**: Yes

**Path Parameters**:
- `vault_id`: (integer, required) ID of the vault item.

**Query Parameters**:
- `master_password`: (string, required) The user's master password.

**Request Body** (all fields optional):
```json
{
  "item_name": "string (optional)",
  "username": "string (optional)",
  "password": "string (optional)",
  "notes": "string (optional)"
}
```

**Response (200 OK)**:
```json
{
  "message": "Vault item updated successfully"
}
```

---

#### DELETE `/api/vault/items/{vault_id}`

Delete a vault item.

**Authorization Header Required**: Yes

**Path Parameters**:
- `vault_id`: (integer, required) ID of the vault item.

**Response (200 OK)**:
```json
{
  "message": "Vault item deleted successfully"
}
```

---

#### GET `/api/vault/categories`

Get all available categories.

**Authorization Header Required**: No (public endpoint)

**Response (200 OK)**:
```json
[
  {
    "category_id": 1,
    "category_name": "Email",
    "description": "Email account credentials",
    "created_at": "2024-07-03T10:00:00"
  },
  {
    "category_id": 2,
    "category_name": "Social Media",
    "description": "Social media credentials",
    "created_at": "2024-07-03T10:00:00"
  },
  {
    "category_id": 3,
    "category_name": "Finance",
    "description": "Financial and banking credentials",
    "created_at": "2024-07-03T10:00:00"
  },
  {
    "category_id": 4,
    "category_name": "Other",
    "description": "Other types of credentials",
    "created_at": "2024-07-03T10:00:00"
  }
]
```

---

### 4. Audit Log Endpoints

#### GET `/api/audit/logs`

Get audit logs.
- Users see only their own logs.
- Auditors see all logs.

**Authorization Header Required**: Yes

**Response (200 OK)**:
```json
[
  {
    "audit_id": 1,
    "action_id": 2,
    "user_id": 1,
    "ip_address": null,
    "user_agent": null,
    "action_details": "User testuser logged in",
    "created_at": "2024-07-03T10:00:00",
    "action_name": "LOGIN_SUCCESS"
  }
]
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 OK | Success |
| 400 Bad Request | Invalid request data |
| 401 Unauthorized | Missing or invalid token |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Server error |

---

## Data Models

### User
```typescript
interface User {
  user_id: number;
  username: string;
  role_name: "User" | "Admin" | "Auditor";
}
```

### Vault Item (Encrypted)
```typescript
interface VaultItem {
  vault_id: number;
  user_id: number;
  category_id: number | null;
  item_name: string;
  encrypted_password: string; // hex string
  iv: string; // hex string
  auth_tag: string; // hex string
  cipher_config_id: number;
  created_at: string; // ISO date
  updated_at: string; // ISO date
  category_name: string | null;
}
```

### Vault Item (Decrypted)
```typescript
interface DecryptedVaultItem {
  vault_id: number;
  item_name: string;
  username: string | null;
  password: string;
  notes: string | null;
}
```

### Category
```typescript
interface Category {
  category_id: number;
  category_name: string;
  description: string;
  created_at: string; // ISO date
}
```

### Audit Log
```typescript
interface AuditLog {
  audit_id: number;
  action_id: number;
  user_id: number | null;
  ip_address: string | null;
  user_agent: string | null;
  action_details: string;
  created_at: string; // ISO date
  action_name: string;
}
```

---

## Running the Backend

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file (copy from `.env.example`) and configure your database settings.

3. Run the server:
   ```bash
   python main.py
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Visit `http://localhost:8000/docs` to explore the interactive API documentation.

---

## Security Notes

1. The master password is **never stored** on the server. It's only used to derive encryption/decryption keys temporarily.
2. All sensitive data is encrypted using AES-256-GCM before being stored in the database.
3. JWT tokens expire after 24 hours by default.
4. Always use HTTPS in production.
