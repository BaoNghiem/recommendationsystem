import subprocess
import sys
import time
import os

def install_dependencies():
    print("--- [SETUP] DANG KIEM TRA VA CAI DAT THU VIEN... ---")
    dependencies = [
        "fastapi",
        "uvicorn",
        "psycopg2-binary",
        "pandas",
        "scikit-learn",
        "numpy"
    ]
    
    for lib in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print(f"OK: {lib}")
        except Exception as e:
            print(f"ERROR: Khong the cai dat {lib}. Chi tiet: {e}")

def run_server():
    print("\n--- [SERVER] DANG KHOI CHAY FASTAPI SERVER... ---")
    print("Vui long cho trong giay lat de load AI Model vao RAM...")
    
    # Dung uvicorn de chay main.py
    # Chung ta goi truc tiep file src/api/main.py
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", "src.api.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload"
        ]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n--- [SERVER] DA DUNG SERVER. ---")
    except Exception as e:
        print(f"--- [SERVER] LOI KHI CHAY SERVER: {e} ---")

if __name__ == "__main__":
    print("==================================================")
    print("   MOVIE RECOMMENDER SYSTEM - AUTO SETUP & RUN   ")
    print("==================================================")
    
    # 1. Cai dat library
    install_dependencies()
    
    # 2. Thong bao Swagger
    print("\n" + "*"*50)
    print("HUONG DAN TRUY CAP:")
    print("- API Root: http://127.0.0.1:8000")
    print("- SWAGGER UI (Test API): http://127.0.0.1:8000/docs")
    print("*"*50 + "\n")
    
    # 3. Chay server
    run_server()
