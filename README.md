
# Secure Personal Data Vault

Ứng dụng quản lý và mã hóa dữ liệu cá nhân nhạy cảm sử dụng AES-GCM và TripleDES.

## Yêu cầu

- Python 3.8+
- Pip

## Cài đặt

1. Clone repository:
   ```bash
   git clone <repository-url>
   cd FortressVault
   ```

2. Cài đặt dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Tạo file `.env` với nội dung sau:
   ```
   MASTER_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   FLASK_SECRET_KEY=your-secret-key
   ```

## Chạy ứng dụng

```bash
python app.py
```

Ứng dụng sẽ chạy trên `http://localhost:5000`

## API Endpoints

- `POST /register`: Đăng ký người dùng mới
  ```json
  {
    "username": "user1",
    "password": "password123",
    "role": "user" // hoặc "admin" / "auditor"
  }
  ```

- `POST /login`: Đăng nhập
  ```json
  {
    "username": "user1",
    "password": "password123"
  }
  ```

- `POST /vault`: Tạo mới dữ liệu nhạy cảm
  ```json
  {
    "data": "My secret data",
    "algorithm": "aes-gcm" // hoặc "3des"
  }
  ```

- `GET /vault`: Lấy danh sách dữ liệu của người dùng hiện tại

- `POST /vault/<id>/decrypt`: Giải mã dữ liệu

- `POST /permissions/grant`: Cấp quyền giải mã (chỉ admin)
  ```json
  {
    "user_id": 1
  }
  ```

- `GET /audit`: Lấy nhật ký kiểm tra

## Chạy kiểm thử

```bash
pytest tests/test_security.py -v
```

## Chức năng

- Mã hóa dữ liệu bằng AES-GCM (chính) hoặc TripleDES (thừa kế)
- Phân quyền người dùng: user, admin, auditor
- Quản lý khóa (MASTER_KEY trong .env)
- Ghi nhật ký kiểm tra cho mọi thao tác giải mã
- Kiểm tra toàn vẹn dữ liệu
- Kiểm tra quyền truy cập

