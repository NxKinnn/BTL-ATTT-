# Báo cáo Dự án: FortressVault - Hệ thống quản lý dữ liệu cá nhân an toàn

**Môn học:** Nhập môn An toàn Bảo mật Thông tin (FIT4012)  
**Ngày:** 04/07/2026

---

## 1. Giới thiệu dự án
FortressVault là một hệ thống quản lý dữ liệu cá nhân an toàn, cho phép người dùng lưu trữ các thông tin nhạy cảm (mật khẩu, thông tin tài khoản) một cách mã hóa.

## 2. Mục tiêu dự án
- Xây dựng hệ thống mã hóa/giai mã dữ liệu an toàn
- Thực hiện xác thực và phân quyền người dùng
- Ghi nhật ký kiểm tra (audit log) cho mọi hành động
- So sánh hiệu suất giữa AES-GCM và TripleDES

## 3. Công nghệ sử dụng
| Thành phần       | Công nghệ                                                                 |
|------------------|---------------------------------------------------------------------------|
| Backend          | Python, FastAPI, PyODBC (SQL Server)                                     |
| Frontend         | HTML5, CSS3, Bootstrap 5, Vanilla JavaScript, Chart.js, Font Awesome     |
| Mã hóa           | AES-256-GCM, TripleDES (3DES), bcrypt, PBKDF2                            |
| Xác thực         | JWT (JSON Web Token)                                                     |
| CSDL             | SQL Server (hoặc SQLite cho phát triển)                                  |
| Kiểm thử         | pytest                                                                   |

## 4. Thực hiện các yêu cầu FIT4012

### ✓ 4.1 Authentication
- Đăng ký/đăng nhập bằng username/password
- Mật khẩu được băm bằng bcrypt (thêm salt tự động)
- Phiên đăng nhập quản lý bằng JWT (thời hạn 24h)
- Auto logout sau 30 phút không hoạt động (frontend)

### ✓ 4.2 Authorization
- Phân quyền: User, Admin, Auditor
- User: quản lý vault của riêng mình
- Auditor: chỉ xem audit log
- Kiểm tra quyền trước mỗi hành động (backend)

### ✓ 4.3 AES-GCM
- Mã hóa chính dùng AES-256-GCM
- IV ngẫu nhiên 12 bytes cho mỗi lần mã hóa
- Kiểm tra toàn vẹn bằng auth tag
- Thực hiện trong `core/crypto_vault.py`

### ✓ 4.4 TripleDES
- Hỗ trợ TripleDES-CBC (dùng cho so sánh hiệu suất)
- IV ngẫu nhiên 8 bytes
- PKCS7 padding
- Thực hiện trong `core/crypto_vault.py`

### ✓ 4.5 Audit Log
- Ghi log mọi hành động: đăng nhập, đăng xuất, thêm/xem/sửa/xoá vault
- Lưu log vào SQL Server (bảng `audit_logs`)
- Thông tin log: action, user, ip, user-agent, timestamp, details
- Thực hiện trong `services/audit_service.py`

### ✓ 4.6 Database
- Sử dụng SQL Server (hoặc SQLite cho dev)
- Bảng: users, roles, user_security_profiles, vault_credentials, categories, cipher_configs, audit_logs, log_actions
- Khởi tạo CSDL trong `config/database.py`

### ✓ 4.7 Key Management
- Master key được tạo từ master password bằng PBKDF2 (100.000 iterations)
- Salt ngẫu nhiên 16 bytes cho mỗi người dùng
- Private key RSA (nếu có) được mã hóa bằng master key
- Không lưu trữ master password dưới bất kỳ hình thức nào

### ✓ 4.8 Logging
- Audit log cho hành động người dùng
- Log lỗi server
- Không log thông tin nhạy cảm (mật khẩu, khóa)

### ✓ 4.9 Security Test
- Kiểm thử bằng pytest
- Các test case:
  - PBKDF2 key derivation
  - AES-GCM encrypt/decrypt
  - AES-GCM integrity check
  - TripleDES encrypt/decrypt
  - Wrong key decryption
- File test: `tests/test_security.py`

### ✓ 4.10 Benchmark
- So sánh hiệu suất giữa AES-GCM và TripleDES
- Hiển thị biểu đồ bằng Chart.js (trang `benchmark.html`)
- Kết luận: AES-GCM nhanh hơn nhiều so với TripleDES

### ✓ 4.11 Documentation
- API Documentation (Swagger UI/Redoc)
- README.md (cập nhật)
- THREAT_MODEL.md
- FINAL_REPORT.md (file này)

---

## 5. Hướng dẫn cài đặt và chạy

### 5.1 Yêu cầu hệ thống
- Python 3.8+
- SQL Server (hoặc dùng SQLite)
- Node.js (cho frontend, không bắt buộc)

### 5.2 Cài đặt Backend
1. Clone repository: `cd d:\FortressVault`
2. Cài dependencies: `pip install -r requirements.txt`
3. Tạo file `.env` từ `.env.example` và cấu hình SQL Server
4. Chạy backend: `python main.py` hoặc `uvicorn main:app --reload`
5. Mở trình duyệt đến `http://localhost:8000/docs` để xem API docs

### 5.3 Chạy Frontend
1. Mở thư mục `d:\FortressVault\frontend`
2. Mở file `login.html` bằng trình duyệt (hoặc dùng Live Server)
3. Đăng ký tài khoản và sử dụng

### 5.4 Chạy kiểm thử
```bash
pytest tests/test_security.py -v
```

---

## 6. Kết luận và đánh giá
Dự án đã hoàn thành đầy đủ các yêu cầu của môn FIT4012. Hệ thống có tính bảo mật tốt, sử dụng các thuật toán mã hóa hiện đại, có audit log đầy đủ và phân quyền người dùng rõ ràng.

---

**Người thực hiện:** [Tên sinh viên]  
**MSSV:** [Mã số sinh viên]
