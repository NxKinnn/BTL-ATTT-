
"""
FortressVault FastAPI Backend
Secure Personal Data Vault with JWT Authentication, AES-256-GCM, TripleDES, and Audit Log
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import traceback
from dotenv import load_dotenv

from services.auth_service import AuthService
from services.vault_service import VaultService
from services.audit_service import AuditService
from core.crypto_vault import CryptoVault

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="FortressVault API",
    description="Secure Personal Data Vault API",
    version="1.0.0",
    debug=True
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("="*80)
    print("UNHANDLED EXCEPTION:")
    print("="*80)
    traceback.print_exc()
    print("="*80)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Pydantic Models
class UserRegister(BaseModel):
    username: str
    password: str

class VaultItemCreate(BaseModel):
    item_name: str
    username: Optional[str] = None
    password: str
    notes: Optional[str] = None
    category_id: Optional[int] = None

class VaultItemUpdate(BaseModel):
    item_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None

# Helper Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role_name: str = payload.get("role_name")
        salt_hex: str = payload.get("salt")
        if username is None or user_id is None:
            raise credentials_exception
        # Convert salt back to bytes
        salt = bytes.fromhex(salt_hex) if salt_hex else None
        return {
            "username": username,
            "user_id": user_id,
            "role_name": role_name,
            "salt": salt
        }
    except JWTError:
        raise credentials_exception

# API Routes
@app.get("/")
async def root():
    return {"message": "FortressVault API", "docs": "/docs"}

# Auth Routes
@app.post("/api/auth/register")
async def register(user: UserRegister, request: Request):
    user_id = AuthService.register_user(
        username=user.username,
        password=user.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists or registration failed"
        )
    return {"message": "Registration successful", "user_id": user_id}

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    user_data = AuthService.login_user(
        username=form_data.username,
        password=form_data.password,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Convert salt to hex for JWT
    salt_hex = user_data['salt'].hex() if user_data.get('salt') else None
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user_data['username'],
            "user_id": user_data['user_id'],
            "role_name": user_data['role_name'],
            "salt": salt_hex
        },
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_data['user_id'],
            "username": user_data['username'],
            "role_name": user_data['role_name']
        }
    }

@app.post("/api/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    AuthService.logout_user(
        user_id=current_user['user_id'],
        username=current_user['username'],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"message": "Logout successful"}

# Vault Routes
@app.get("/api/vault/items")
async def get_vault_items(current_user: dict = Depends(get_current_user)):
    return VaultService.get_user_vault_items(user_id=current_user['user_id'], role=current_user['role_name'])

@app.post("/api/vault/items")
async def add_vault_item(
    item: VaultItemCreate,
    master_password: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user['role_name'] != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    # Derive master key
    master_key = CryptoVault.derive_master_key(master_password, current_user['salt'])
    vault_id = VaultService.add_vault_item(
        user_id=current_user['user_id'],
        item_name=item.item_name,
        master_key=master_key,
        username=item.username,
        password=item.password,
        notes=item.notes,
        category_id=item.category_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    if not vault_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add vault item"
        )
    return {"message": "Vault item added successfully", "vault_id": vault_id}

@app.get("/api/vault/items/{vault_id}")
async def get_vault_item(
    vault_id: int,
    master_password: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user['role_name'] != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    master_key = CryptoVault.derive_master_key(master_password, current_user['salt'])
    item = VaultService.decrypt_vault_item(
        user_id=current_user['user_id'],
        role=current_user['role_name'],
        vault_id=vault_id,
        master_key=master_key,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault item not found or decryption failed"
        )
    return item

@app.put("/api/vault/items/{vault_id}")
async def update_vault_item(
    vault_id: int,
    item_update: VaultItemUpdate,
    master_password: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user['role_name'] != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    master_key = CryptoVault.derive_master_key(master_password, current_user['salt'])
    success = VaultService.update_vault_item(
        user_id=current_user['user_id'],
        role=current_user['role_name'],
        vault_id=vault_id,
        master_key=master_key,
        item_name=item_update.item_name,
        username=item_update.username,
        password=item_update.password,
        notes=item_update.notes,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault item not found or update failed"
        )
    return {"message": "Vault item updated successfully"}

@app.delete("/api/vault/items/{vault_id}")
async def delete_vault_item(
    vault_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user['role_name'] != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )
    success = VaultService.delete_vault_item(
        user_id=current_user['user_id'],
        role=current_user['role_name'],
        vault_id=vault_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vault item not found or deletion failed"
        )
    return {"message": "Vault item deleted successfully"}

@app.get("/api/vault/categories")
async def get_categories():
    return VaultService.get_categories()

# Audit Log Routes
@app.get("/api/audit/logs")
async def get_audit_logs(current_user: dict = Depends(get_current_user)):
    return AuditService.get_logs(
        user_id=current_user['user_id'],
        role=current_user['role_name']
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

