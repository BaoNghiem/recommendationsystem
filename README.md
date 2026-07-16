# 🎬 Hệ thống Gợi ý Phim (Movie Recommendation System)

Đồ án tốt nghiệp — Hệ thống gợi ý phim sử dụng **Hybrid AI** (FunkSVD + Content-Based Filtering), backend FastAPI, frontend React.

---

## 📋 Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| RAM | 4 GB (8 GB khuyến nghị) |

---

## 🗂️ Cấu trúc thư mục

```
Bài đồ án/
├── start.py                # ⭐ Script khởi động all-in-one
├── main_train.py           # Train lại AI model (nếu cần)
├── requirements.txt        # Thư viện Python
├── .env.example            # Mẫu cấu hình môi trường
│
├── src/
│   ├── api/                # FastAPI backend
│   │   ├── main.py         # Entry point server
│   │   ├── routes/         # Tất cả API endpoints
│   │   ├── engine_wrapper.py   # Wrapper AI Engine (load/retrain)
│   │   └── auth/           # JWT authentication
│   ├── models/             # AI models (FunkSVD, Content-Based, Hybrid)
│   ├── data/               # DataLoader & Preprocessor
│   ├── features/           # Feature engineering
│   ├── evaluation/         # Đánh giá mô hình (RMSE, MAE, NDCG)
│   └── database/
│       ├── db_config.py    # Kết nối PostgreSQL
│       └── schema.sql      # Schema database (11 bảng)
│
├── frontend/               # React + Vite + TailwindCSS
│
├── scripts/
│   ├── movie_db_dump.sql   # ⭐ Dump DB (~28 MB) — KHÔNG có trong repo, xem Bước 3
│   ├── restore_db.py       # ⭐ Restore database từ dump
│   ├── dump_db.py          # Tạo dump mới (dùng khi backup)
│   └── setup_and_run.py    # Khởi động backend đơn lẻ (không có frontend)
│
├── data/ml-1m/             # Dataset MovieLens 1M (nguồn train AI)
├── output/models/          # Model đã train (.pkl) — cần có khi chạy
└── uploads/                # Poster + video upload — KHÔNG commit lên git
```

> **⚠️ Lưu ý về dữ liệu:** File `scripts/movie_db_dump.sql` (~28 MB) **không được lưu trong repo** do vượt giới hạn GitHub.  
> Bạn phải có file này riêng (liên hệ tác giả hoặc tự xuất từ máy gốc bằng `python scripts/dump_db.py`).

---

## ⚙️ Hướng dẫn cài đặt (máy mới)

### Bước 1 — Cài đặt thư viện Python

```bash
# Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# Kích hoạt (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Cài thư viện
pip install -r requirements.txt
```

### Bước 2 — Cấu hình môi trường

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Mở `.env` và điền các thông tin sau:

```env
JWT_SECRET_KEY=any-random-secret-string-here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=movie_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_16char_app_password
```

> **Lưu ý:** `MAIL_USERNAME` / `MAIL_PASSWORD` dùng để gửi email xác nhận tài khoản.  
> Nếu chỉ chạy demo, có thể để placeholder — tính năng đăng ký sẽ vẫn hoạt động (email sẽ không được gửi đi).

### Bước 3 — Tạo database và restore dữ liệu

**3a. Tạo database trống trong PostgreSQL:**

```sql
-- Trong psql hoặc pgAdmin:
CREATE DATABASE movie_db;
```

**3b. Lấy file dump SQL:**

File `scripts/movie_db_dump.sql` (~28 MB) **không được lưu trong repo** do vượt giới hạn GitHub.  
Bạn cần lấy file này theo một trong hai cách:

- **Cách 1 (khuyến nghị):** Tải file `movie_db_dump.sql` từ liên kết mà tác giả cung cấp (Google Drive / email), rồi đặt vào thư mục `scripts/`.
- **Cách 2 (nếu có máy gốc):** Chạy lệnh sau trên máy gốc để xuất dump:
  ```bash
  python scripts/dump_db.py
  ```

**3c. Restore dữ liệu:**

```bash
python scripts/restore_db.py
```

> Script này đọc thông tin kết nối từ `.env` và tự động restore file `scripts/movie_db_dump.sql` (chứa toàn bộ phim, ratings, diễn viên, đạo diễn).

### Bước 4 — (Tùy chọn) Tạo tài khoản Admin

Đăng ký tài khoản thường qua giao diện web, sau đó nâng quyền admin trong database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your_email@example.com';
```

---

## 🚀 Khởi động hệ thống

```bash
python start.py
```

Script này sẽ tự động:
1. Kiểm tra file `.env`
2. Kiểm tra AI model trong `output/models/` (tự train nếu chưa có — ~10-30 phút)
3. Cài `npm install` nếu `node_modules` chưa có
4. Khởi động **Backend** tại `http://127.0.0.1:8000`
5. Khởi động **Frontend** tại `http://localhost:5173`

Nhấn `Ctrl+C` để tắt cả hai server.

---

## 🔗 URL truy cập

| URL | Mô tả |
|---|---|
| `http://localhost:5173` | Giao diện web người dùng |
| `http://127.0.0.1:8000` | API backend |
| `http://127.0.0.1:8000/docs` | Swagger UI (test API) |

---

## 📡 API Endpoints chính

| Endpoint | Mô tả |
|---|---|
| `POST /auth/register` | Đăng ký tài khoản |
| `POST /auth/login` | Đăng nhập, nhận JWT |
| `GET /movies/` | Danh sách phim |
| `GET /movies/search?q=...` | Tìm kiếm phim, đạo diễn, diễn viên |
| `GET /recommend/{user_id}` | Gợi ý phim AI (Hybrid) |
| `GET /popular` | Phim phổ biến nhất |
| `GET /trending` | Phim đang hot |
| `PUT /watch/progress` | Lưu tiến độ xem (cần login) |
| `GET /watch/history` | Lịch sử xem (cần login) |
| `POST /admin/movies/{id}/video` | Upload video (admin, tối đa 2.5 GB) |

---

## 🛠️ Xử lý lỗi thường gặp

| Lỗi | Giải pháp |
|---|---|
| `Cannot connect to Database` | Kiểm tra PostgreSQL đang chạy và thông tin `.env` đúng |
| `AI Engine không tải được model` | Đảm bảo `output/models/` có file `.pkl`. Chạy `python main_train.py` nếu cần |
| Frontend báo lỗi CORS | Đảm bảo backend đang chạy ở port 8000 |
| Lỗi 413 khi upload video | File không được vượt quá 2.5 GB |
| `npm: command not found` | Cài Node.js 18+ từ https://nodejs.org |

---

## 🧠 Công nghệ sử dụng

| Tầng | Công nghệ |
|---|---|
| **Backend** | FastAPI, Uvicorn, Python 3.10+ |
| **Database** | PostgreSQL 14+ |
| **AI Engine** | FunkSVD (Collaborative Filtering), Cosine Similarity (Content-Based), Hybrid Recommender |
| **Frontend** | React 18, Vite, TailwindCSS, Framer Motion, Lucide Icons |
| **Auth** | JWT (HS256), bcrypt |
| **Video** | HTTP Range Requests (streaming 206 Partial Content) |
