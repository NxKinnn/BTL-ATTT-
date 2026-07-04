# Hướng dẫn Demo FortressVault

## Bước 1: Chuẩn bị môi trường
1. Đảm bảo cài đặt Python 3.8+ và SQL Server (hoặc dùng SQLite)
2. Cài đặt dependencies: `pip install -r requirements.txt`
3. Tạo file `.env` và cấu hình SQL Server

## Bước 2: Chạy Backend
```bash
cd d:\FortressVault
python main.py
```
- Mở trình duyệt đến `http://localhost:8000/docs` để xem API docs

## Bước 3: Chạy Frontend
- Mở thư mục `d:\FortressVault\frontend`
- Mở file `index.html` (hoặc dùng Live Server VS Code)

## Bước 4: Thực hiện các chức năng
1. **Đăng ký tài khoản**: Nhập username và password
2. **Đăng nhập**: Sử dụng tài khoản vừa đăng ký
3. **Xem Dashboard**: Thống kê vault, categories, recent activity
4. **Thêm Vault Item**:
   - Nhập item name, username, password, notes
   - Nhập master password để mã hóa
   - Nhấn "Save Item"
5. **Xem/Giải mã Vault Item**:
   - Nhấn nút "View"
   - Nhập master password để giải mã
   - Nhấn "Show Password" để xem mật khẩu
6. **Xoá Vault Item**: Nhấn "Delete" và xác nhận
7. **Xem Audit Log**: Mở trang "Audit Log"
8. **Xem Benchmark**: Mở trang "Benchmark" và nhấn "Run Benchmark"
9. **Đăng xuất**: Nhấn "Logout"

## Bước 5: Chạy kiểm thử an ninh
```bash
pytest tests/test_security.py -v
```
