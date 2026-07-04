# FortressVault - Secure Personal Data Vault

Ứng dụng quản lý và mã hóa dữ liệu cá nhân nhạy cảm sử dụng AES-GCM và TripleDES.

---

## Yêu cầu hệ thống
- Python 3.8+
- SQL Server (hoặc SQLite cho phát triển)
- Pip

---

## Cài đặt và chạy

### 1. Cài đặt Backend
```bash
cd d:\FortressVault
pip install -r requirements.txt
```

### 2. Cấu hình môi trường
Tạo file `.env` (sao chép từ `.env.example`):
```env
# SQL Server Configuration
SQL_SERVER=localhost\SQLEXPRESS
SQL_DATABASE=FortressVault_Core
SQL_USERNAME=sa
SQL_PASSWORD=YourStrongPassword123!
SQL_DRIVER={ODBC Driver 17 for SQL Server}

# JWT Secret Key (đổi trong production!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-please
```

### 3. Chạy Backend
```bash
python main.py
```
Backend sẽ chạy trên `http://localhost:8000`  
Xem API documentation tại `http://localhost:8000/docs`

### 4. Chạy Frontend
- Mở thư mục `frontend`
- Mở file `index.html` bằng trình duyệt (hoặc dùng Live Server extension VS Code)

---

## Chức năng chính
- ✅ **Authentication**: Đăng ký, đăng nhập, đăng xuất (JWT)
- ✅ **Authorization**: Phân quyền User/Admin/Auditor
- ✅ **Vault Management**: Thêm, xem, sửa, xoá, giải mã dữ liệu
- ✅ **AES-256-GCM**: Mã hóa dữ liệu chính (an toàn, nhanh)
- ✅ **TripleDES**: Mã hóa phụ (dùng cho so sánh hiệu suất)
- ✅ **Audit Log**: Ghi log mọi hành động người dùng
- ✅ **Dashboard**: Thống kê vault, categories, recent activity
- ✅ **Benchmark**: So sánh hiệu suất AES vs 3DES (Chart.js)
- ✅ **Responsive Design**: Hỗ trợ Desktop/Tablet/Mobile

---

## Kiểm thử (Security Test)
```bash
pytest tests/test_security.py -v
```

---

## Cấu trúc thư mục
```
d:\FortressVault\
├── config\              # Cấu hình CSDL
├── core\                # Mã hóa (crypto_vault.py)
├── services\            # Business logic (auth, vault, audit)
├── tests\               # Kiểm thử an ninh
├── frontend\            # Giao diện người dùng
│   ├── assets\
│   │   ├── css\
│   │   ├── js\
│   │   └── images\
│   ├── login.html
│   ├── dashboard.html
│   ├── vault.html
│   └── ...
├── docs\                # Tài liệu (threat model, report)
├── main.py              # FastAPI backend
├── requirements.txt
└── README.md
```

---

## Tài liệu tham khảo
- [API Documentation](API_DOCUMENTATION.md)
- [Threat Model & STRIDE Analysis](docs/THREAT_MODEL.md)
- [Final Report](docs/FINAL_REPORT.md)

---

## Công nghệ sử dụng
| Thể loại          | Công nghệ                                                                 |
|--------------------|---------------------------------------------------------------------------|
| Backend Framework  | FastAPI                                                                   |
| Authentication     | JWT (python-jose)                                                        |
| Database           | SQL Server (PyODBC)                                                      |
| Encryption         | cryptography (AES-256-GCM, TripleDES), bcrypt, PBKDF2                    |
| Frontend           | Bootstrap 5, Font Awesome, Chart.js                                      |
| Testing            | pytest                                                                   |
