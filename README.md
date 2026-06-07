# 🎬 Movie Recommender System

Hệ thống gợi ý phim sử dụng **FunkSVD + Content-Based Hybrid AI**, backend FastAPI, frontend React.

---

## 📋 Yêu cầu hệ thống

| Thành phần | Phiên bản |
|-----------|-----------|
| Python | 3.10+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| Git | Bất kỳ |

---

## 🚀 Cài đặt trên máy mới

### Bước 1 — Clone repo

```bash
git clone https://github.com/BaoNghiem/recommendationsystem.git
cd recommendationsystem
```

### Bước 2 — Cấu hình môi trường

```bash
# Tạo file .env từ template
copy .env.example .env   # Windows
# hoặc: cp .env.example .env  (Linux/Mac)
```

Mở `.env` và điền thông tin thực:
- `DB_PASSWORD` — mật khẩu PostgreSQL của bạn
- `JWT_SECRET_KEY` — chuỗi bí mật bất kỳ (≥ 32 ký tự)
- `SMTP_EMAIL` / `SMTP_PASSWORD` — tài khoản Gmail + App Password

### Bước 3 — Cài Python dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# hoặc: source venv/bin/activate  (Linux/Mac)

pip install -r requirements.txt
```

### Bước 4 — Tạo và restore Database

```bash
# Tạo database trống
psql -U postgres -c "CREATE DATABASE movie_db;"

# Nhận file dump từ người dùng cũ (xem mục bên dưới)
# Đặt file vào: scripts/movie_db_dump.sql

# Restore
python scripts/restore_db.py
```

> **Lấy file dump từ đâu?** Người dùng máy gốc chạy `python scripts/dump_db.py` → chia sẻ file `scripts/movie_db_dump.sql` qua USB/Google Drive/Zalo.

### Bước 5 — Chạy Backend

```bash
# Kích hoạt venv trước
venv\Scripts\activate

uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend sẽ tự load AI model từ `output/models/funksvd_model.pkl`.

### Bước 6 — Chạy Frontend

```bash
cd frontend
npm install
npm run dev
```

Mở trình duyệt: **http://localhost:5173**

---

## 📁 Cấu trúc thư mục

```
├── config/          — Cấu hình paths
├── data/ml-1m/      — Dataset MovieLens 1M gốc
├── frontend/        — React + Vite UI
├── output/
│   └── models/      — Model AI đã train (funksvd_model.pkl)
├── scripts/         — Migration, dump/restore DB, admin utils
├── src/
│   ├── api/         — FastAPI backend
│   ├── data/        — Data loader & preprocessor
│   ├── database/    — DB config & SQL schemas
│   ├── models/      — FunkSVD, Content-Based, Hybrid
│   └── evaluation/  — RMSE, MAE, NDCG evaluator
├── tests/           — Integration tests (4 phases)
├── uploads/posters/ — Ảnh poster phim
└── main_train.py    — Script train lại model
```

---

## 🔄 Chuyển dữ liệu giữa máy

### Máy gốc → Xuất DB

```bash
python scripts/dump_db.py
# Tạo ra: scripts/movie_db_dump.sql (~28MB)
```

### Máy mới → Nhập DB

```bash
# Đặt file movie_db_dump.sql vào thư mục scripts/
python scripts/restore_db.py
```

> ⚠️ File `movie_db_dump.sql` **không được commit** lên GitHub vì chứa dữ liệu thực (email, ratings). Chia sẻ qua kênh riêng.

---

## 🧠 Train lại model

```bash
# Train FunkSVD từ đầu (mất ~5-10 phút)
python main_train.py
```

---

## 🧪 Chạy kiểm thử

```bash
# Chạy toàn bộ 4 phases (cần backend đang chạy)
python tests/run_all_tests.py
```
