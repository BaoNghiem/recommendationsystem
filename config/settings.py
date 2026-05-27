from pathlib import Path

# Thư mục gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent

# Thư mục chứa dữ liệu
DATA_DIR = BASE_DIR / 'data'

# Thư mục lưu kết quả xuất ra (ảnh EDA, logs, mô hình)
OUTPUT_DIR = BASE_DIR / 'output'
EDA_OUTPUT_DIR = OUTPUT_DIR / 'eda'
MODEL_OUTPUT_DIR = OUTPUT_DIR / 'models'

# Tạo sẵn các thư mục nếu chưa tồn tại
EDA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Đường dẫn đến các file dữ liệu cụ thể (MovieLens 1M)
RATINGS_PATH = DATA_DIR / 'ml-1m' / 'ratings.dat'
MOVIES_PATH = DATA_DIR / 'ml-1m' / 'movies.dat'
USERS_PATH = DATA_DIR / 'ml-1m' / 'users.dat'
