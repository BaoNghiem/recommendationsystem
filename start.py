"""
start.py — Khởi động toàn bộ hệ thống Movie Recommender
=========================================================
Chạy lệnh này để khởi động cả Backend (FastAPI) lẫn Frontend (React):

    python start.py

Yêu cầu trước khi chạy:
  1. PostgreSQL đang chạy, database 'movie_db' đã được restore
  2. File .env đã được tạo từ .env.example và điền đúng thông tin
  3. Node.js 18+ đã cài đặt (để chạy frontend)

Xem README.md để biết hướng dẫn cài đặt chi tiết.
"""
import subprocess
import sys
import os
import time
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ─── Màu terminal ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def info(msg):    print(f"{CYAN}[INFO]{RESET} {msg}")
def ok(msg):      print(f"{GREEN}[OK]{RESET}   {msg}")
def warn(msg):    print(f"{YELLOW}[WARN]{RESET} {msg}")
def error(msg):   print(f"{RED}[ERR]{RESET}  {msg}")
def header(msg):  print(f"\n{BOLD}{msg}{RESET}")

# ─── Kiểm tra file .env ──────────────────────────────────────────────────────
def check_env():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        error("Chưa có file .env!")
        warn("Tạo file .env từ mẫu:")
        print("    copy .env.example .env   (Windows)")
        print("    cp .env.example .env     (macOS/Linux)")
        print("Sau đó điền DB_PASSWORD và JWT_SECRET_KEY vào file .env.")
        sys.exit(1)
    ok(".env tìm thấy")

# ─── Kiểm tra output/models ──────────────────────────────────────────────────
def check_models():
    model_dir = BASE_DIR / "output" / "models"
    model_file = model_dir / "funksvd_model.pkl"
    mapping_file = model_dir / "id_mappings.pkl"

    if model_file.exists() and mapping_file.exists():
        ok(f"AI model đã có sẵn ({model_file.stat().st_size / 1e6:.1f} MB)")
        return

    warn("Chưa có file model trong output/models/. Đang train...")
    warn("Quá trình này có thể mất 10-30 phút...")
    try:
        subprocess.run([sys.executable, str(BASE_DIR / "main_train.py")], check=True)
        ok("Train model hoàn tất!")
    except subprocess.CalledProcessError:
        error("Train model thất bại. Kiểm tra lại dataset trong thư mục data/ml-1m/")
        sys.exit(1)

# ─── Cài đặt npm nếu chưa có node_modules ────────────────────────────────────
def check_frontend_deps():
    node_modules = BASE_DIR / "frontend" / "node_modules"
    if node_modules.exists():
        ok("Frontend dependencies đã có sẵn")
        return

    info("Chưa có node_modules, đang chạy npm install...")
    if not shutil.which("npm"):
        error("npm không tìm thấy. Cài Node.js 18+ từ https://nodejs.org/")
        sys.exit(1)
    try:
        subprocess.run(["npm", "install"], cwd=BASE_DIR / "frontend", check=True, shell=True)
        ok("npm install hoàn tất!")
    except subprocess.CalledProcessError:
        error("npm install thất bại.")
        sys.exit(1)

# ─── Khởi động Backend ───────────────────────────────────────────────────────
def start_backend():
    info("Đang khởi động Backend (FastAPI)...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
    ]
    # Chạy trong cùng thư mục gốc để import đúng
    proc = subprocess.Popen(cmd, cwd=BASE_DIR)
    return proc

# ─── Khởi động Frontend ──────────────────────────────────────────────────────
def start_frontend():
    info("Đang khởi động Frontend (React + Vite)...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=BASE_DIR / "frontend",
    )
    return proc

# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"{BOLD}   🎬 MOVIE RECOMMENDER SYSTEM — STARTUP{RESET}")
    print("=" * 60)

    # Bước 1: Kiểm tra điều kiện
    header("Bước 1/4 — Kiểm tra môi trường")
    check_env()

    # Bước 2: Kiểm tra model AI
    header("Bước 2/4 — Kiểm tra AI Model")
    check_models()

    # Bước 3: Cài đặt frontend nếu cần
    header("Bước 3/4 — Kiểm tra Frontend")
    check_frontend_deps()

    # Bước 4: Khởi động cả hai server
    header("Bước 4/4 — Khởi động servers")
    backend_proc  = start_backend()
    time.sleep(2)   # Đợi backend ổn định trước khi mở frontend
    frontend_proc = start_frontend()

    print("\n" + "=" * 60)
    print(f"{GREEN}{BOLD}✅ Hệ thống đã khởi động!{RESET}")
    print(f"   🔗 Frontend  : http://localhost:5173")
    print(f"   🔗 Backend   : http://127.0.0.1:8000")
    print(f"   📖 API Docs  : http://127.0.0.1:8000/docs")
    print(f"\n   Nhấn Ctrl+C để tắt cả hai server.")
    print("=" * 60 + "\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n[STOP] Đang tắt servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("[STOP] Đã tắt. Tạm biệt!")


if __name__ == "__main__":
    main()
