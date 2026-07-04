# FortressVault - Threat Model & STRIDE Analysis

## Giới thiệu
Tài liệu này phân tích các mối đe dọa an ninh cho ứng dụng FortressVault theo mô hình STRIDE.

---

## 1. STRIDE Analysis

| Mối đe dọa        | Mô tả                                                                 | Phân loại       | Giải pháp hiện tại                                                                 | Đề xuất cải thiện                                                                 |
|--------------------|-----------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Spoofing**       | Giả mạo danh tính người dùng                                         | Authentication | - Đăng nhập bằng username/password<br>- Mật khẩu được băm bằng bcrypt             | - Thêm 2FA (Two-Factor Authentication)<br>- Giới hạn số lần đăng nhập thất bại   |
| **Tampering**      | Chỉnh sửa dữ liệu (cơ sở dữ liệu, dữ liệu mã hóa)                    | Integrity      | - Dữ liệu được mã hóa bằng AES-GCM (có kiểm tra toàn vẹn auth tag)               | - Thêm checksum cho file cấu hình<br>- Ký số các audit logs với khóa riêng       |
| **Repudiation**    | Người dùng phủ nhận đã thực hiện hành động                            | Non-repudiation | - Tất cả hành động đều được ghi vào audit log                                     | - Thêm chữ ký số cho mỗi bản ghi audit log<br>- Lưu audit log vào hệ thống tệp chỉ ghi (write-only) |
| **Information Disclosure** | Tiết lộ thông tin nhạy cảm (mật khẩu, khóa)               | Confidentiality | - Dữ liệu vault mã hóa bằng AES-GCM<br>- Mật khẩu người dùng băm bcrypt          | - Không log thông tin nhạy cảm<br>- Thêm rate limiting cho API解密<br>- Sử dụng HTTPS cho toàn bộ giao tiếp |
| **Denial of Service** | Làm cho dịch vụ không khả dụng                                | Availability   | - Không có giới hạn tốc độ truy cập hiện tại                                      | - Thêm rate limiting cho API<br>- Sử dụng kết nối cơ sở dữ liệu bền bỉ (pooling) |
| **Elevation of Privilege** | Nâng quyền truy cập trái phép                      | Authorization  | - Phân quyền người dùng: User, Admin, Auditor<br>- Kiểm tra role trước mỗi hành động | - Thêm kiểm tra quyền chi tiết (RBAC)<br>- Log mọi hành động thay đổi quyền       |

---

## 2. DFD (Data Flow Diagram)
```
┌──────────┐     ┌───────────┐     ┌─────────────────┐
│  Người  │────▶│  Frontend │────▶│  Backend API   │
│  Dùng   │     │  (Web/UI) │     │  (FastAPI)     │
└──────────┘     └───────────┘     └────────┬────────┘
                                           │
                                           ▼
                              ┌─────────────────────┐
                              │  SQL Server (DB)    │
                              └─────────────────────┘
```

---

## 3. Danh sách các tài sản cần bảo vệ
1. Dữ liệu vault của người dùng (mật khẩu, thông tin cá nhân)
2. Master key (dùng để mã hóa/giải mã dữ liệu)
3. Thông tin tài khoản người dùng (username, password hash)
4. Audit logs
5. Cơ sở dữ liệu

---

## 4. Kết luận
Ứng dụng đã thực hiện các biện pháp bảo vệ cơ bản, nhưng cần bổ sung thêm:
- HTTPS cho production
- 2FA
- Rate limiting
- RBAC chi tiết hơn
