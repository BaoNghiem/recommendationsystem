# 🎬 Hệ thống Gợi ý Phim (Movie Recommendation System)

Đồ án tốt nghiệp — Hệ thống gợi ý phim sử dụng Hybrid AI (FunkSVD + Content-Based Filtering).

---

## 📋 Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| RAM | 4 GB (8 GB khuyến nghị) |
| Dung lượng disk | 10 GB+ (để lưu video upload) |

---

## 🗂️ Cấu trúc thư mục

```
Bài đồ án/
├── frontend/               # React + Vite
│   ├── src/
│   └── package.json
├── src/
│   ├── api/                # FastAPI backend
│   │   ├── main.py         # Entry point
│   │   ├── routes/         # Tất cả API endpoints
│   │   ├── engine_wrapper.py   # Wrapper cho AI Engine
│   │   └── auth/           # JWT authentication
│   ├── models/             # AI model (Hybrid Recommender)
│   ├── data/               # DataLoader
│   └── database/
│       ├── db_config.py    # Kết nối PostgreSQL
│       └── schema.sql      # Schema database đầy đủ (11 bảng)
├── uploads/                # File upload (poster + video) — KHÔNG commit lên git
│   ├── posters/
│   └── videos/
├── data/                   # Dataset MovieLens 1M
├── output/                 # Model đã train (.pkl files)
├── venv/                   # Python virtual environment — KHÔNG commit lên git
├── .env                    # Biến môi trường — KHÔNG commit lên git
├── .env.example            # Mẫu .env
└── requirements.txt
```

---

## ⚙️ Hướng dẫn cài đặt từ đầu (máy mới)

### Bước 1 — Clone repository

```bash
git clone <repository-url>
cd "Bài đồ án"
```

### Bước 2 — Tạo và kích hoạt môi trường ảo Python

```bash
# Tạo venv
python -m venv venv

# Kích hoạt (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Kích hoạt (Windows CMD)
venv\Scripts\activate.bat

# Kích hoạt (macOS/Linux)
source venv/bin/activate
```

### Bước 3 — Cài đặt dependencies Python

```bash
pip install -r requirements.txt
```

### Bước 4 — Cấu hình biến môi trường

```bash
# Sao chép file mẫu
copy .env.example .env      # Windows
cp .env.example .env        # macOS/Linux
```

Sau đó mở `.env` và điền thông tin:

```env
# JWT — Tạo key ngẫu nhiên mạnh
JWT_SECRET_KEY=your-super-secret-key-change-this

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=movie_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Email (để gửi email xác nhận — có thể bỏ qua khi dev)
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_16char_app_password
```

### Bước 5 — Tạo database PostgreSQL

```sql
-- Mở psql hoặc pgAdmin rồi chạy:
CREATE DATABASE movie_db;
```

Sau đó import schema:

```bash
psql -U postgres -d movie_db -f src/database/schema.sql
```

> **Lưu ý:** Nếu có file `migration_phase3.sql`, chạy thêm:
> ```bash
> psql -U postgres -d movie_db -f src/database/migration_phase3.sql
> ```

### Bước 6 — Restore dữ liệu (nếu chuyển máy)

Nếu có file dump database từ máy cũ:

```bash
pg_restore -U postgres -d movie_db backup.dump
# hoặc nếu là file .sql:
psql -U postgres -d movie_db < backup.sql
```

### Bước 7 — Copy file model đã train

Thư mục `output/` chứa các file `.pkl` model đã train (FunkSVD, Content-Based matrix). Nếu chuyển máy, copy nguyên thư mục `output/` sang.

Nếu không có file model, chạy lại training:

```bash
python main_train.py
```

> ⚠️ Training mất khoảng 10-30 phút tùy máy.

### Bước 8 — Copy file uploads (poster + video)

Copy thư mục `uploads/` từ máy cũ sang (thư mục này không được commit lên git vì quá nặng).

```bash
# Cấu trúc:
uploads/
├── posters/    # Ảnh poster phim
└── videos/     # File video phim (có thể lên đến 2.5 GB/file)
```

---

## 🚀 Chạy ứng dụng

### Backend (FastAPI)

```bash
# Kích hoạt venv trước
.\venv\Scripts\Activate.ps1

# Chạy backend
.\venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --port 8000
```

Backend khởi động tại: `http://127.0.0.1:8000`  
API docs (Swagger): `http://127.0.0.1:8000/docs`

### Frontend (React + Vite)

```bash
cd frontend

# Lần đầu — cài dependencies
npm install

# Chạy dev server
npm run dev
```

Frontend khởi động tại: `http://localhost:5173`

---

## 🔑 Tài khoản mặc định

Sau khi import dữ liệu, có thể tạo admin bằng cách đăng ký tài khoản rồi update role trực tiếp trong DB:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your_email@example.com';
```

---

## 📡 API Endpoints chính

| Endpoint | Mô tả |
|---|---|
| `POST /auth/register` | Đăng ký tài khoản |
| `POST /auth/login` | Đăng nhập, nhận JWT |
| `GET /movies/` | Danh sách phim |
| `GET /movies/search?q=...` | Tìm kiếm phim, đạo diễn, diễn viên |
| `GET /recommend/{user_id}` | Gợi ý phim AI cho user |
| `GET /popular` | Phim phổ biến nhất |
| `GET /trending` | Phim đang hot |
| `PUT /watch/progress` | Lưu tiến độ xem (cần login) |
| `GET /watch/history` | Lịch sử xem (cần login) |
| `POST /admin/movies/{id}/video` | Upload video (admin, tối đa 2.5 GB) |

---

## 🎥 Upload Video

- Hỗ trợ định dạng: `mp4`, `webm`, `mkv`, `avi`, `mov`
- Kích thước tối đa: **2.5 GB**
- Upload sử dụng **streaming chunk** (8 MB/chunk), không load toàn bộ file vào RAM
- Cần đăng nhập bằng tài khoản **admin**

---

## 🛠️ Xử lý lỗi thường gặp

### Lỗi kết nối database
```
Cannot connect to Database
```
→ Kiểm tra PostgreSQL đang chạy và thông tin trong `.env` đúng.

### Lỗi import model
```
AI Engine không tải được model
```
→ Đảm bảo thư mục `output/` có đầy đủ file `.pkl`. Chạy lại `python main_train.py` nếu cần.

### Frontend báo lỗi CORS
→ Đảm bảo backend đang chạy ở port 8000. Kiểm tra `VITE_API_URL` trong `frontend/.env` (nếu có).

### Upload video lỗi 413
→ Đảm bảo backend đang chạy với `--reload` flag đúng cách. File không được vượt 2.5 GB.

---

## 📦 Chuyển máy — Checklist

- [ ] Clone git repository
- [ ] Tạo venv và cài `pip install -r requirements.txt`
- [ ] Copy file `.env` (hoặc tạo mới từ `.env.example`)
- [ ] Tạo database PostgreSQL, import `schema.sql`
- [ ] Restore dữ liệu từ backup DB
- [ ] Copy thư mục `output/` (AI model)
- [ ] Copy thư mục `uploads/` (poster + video)
- [ ] `cd frontend && npm install`
- [ ] Chạy backend: `.\venv\Scripts\python.exe -m uvicorn src.api.main:app --reload --port 8000`
- [ ] Chạy frontend: `npm run dev`

---

## 🧠 Công nghệ sử dụng

**Backend:** FastAPI, PostgreSQL, Python 3.10+  
**AI Engine:** FunkSVD (Collaborative Filtering), Cosine Similarity (Content-Based), Hybrid Recommender  
**Frontend:** React 18, Vite, Framer Motion, Lucide Icons, TailwindCSS  
**Auth:** JWT (HS256), bcrypt password hashing  
**Video Streaming:** HTTP Range Requests (206 Partial Content)
