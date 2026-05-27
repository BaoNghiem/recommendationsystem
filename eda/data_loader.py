"""
data_loader.py
==============
Module chịu trách nhiệm load và làm sạch toàn bộ 3 file dữ liệu
của tập MovieLens 1M: ratings.dat, movies.dat, users.dat.

Tác giả  : Senior AI Engineer
Mục đích : Đồ án tốt nghiệp — Movie Recommender System
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ─────────────────────────────────────────────
#  Đường dẫn gốc tới thư mục data/ml-1m
# ─────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "ml-1m"


def load_ratings(path: Path | None = None) -> pd.DataFrame:
    """
    Load file ratings.dat.

    Schema  : UserID :: MovieID :: Rating :: Timestamp
    Rating  : 1–5 sao (integer)
    Returns : DataFrame với các cột [user_id, movie_id, rating, timestamp]
    """
    path = path or DATA_DIR / "ratings.dat"

    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        names=["user_id", "movie_id", "rating", "timestamp"],
        dtype={
            "user_id":   np.int32,
            "movie_id":  np.int32,
            "rating":    np.int8,
            "timestamp": np.int64,
        },
    )

    # Kiểm tra và báo cáo missing values
    n_missing = df.isnull().sum().sum()
    if n_missing > 0:
        print(f"[WARN] ratings.dat có {n_missing} missing values — đang drop...")
        df.dropna(inplace=True)
    else:
        print(f"[OK]   ratings.dat  — {len(df):,} dòng, 0 missing values.")

    # Validate khoảng rating hợp lệ
    invalid = df[~df["rating"].between(1, 5)]
    if len(invalid) > 0:
        print(f"[WARN] Có {len(invalid)} rating ngoài khoảng [1,5] — đang drop...")
        df = df[df["rating"].between(1, 5)]

    return df.reset_index(drop=True)


def load_movies(path: Path | None = None) -> pd.DataFrame:
    """
    Load file movies.dat.

    Schema  : MovieID :: Title :: Genres  (pipe-separated genres)
    Returns : DataFrame với các cột [movie_id, title, genres]
              Trong đó 'genres' vẫn là chuỗi gốc, việc one-hot sẽ
              được thực hiện ở feature_engineering.py.
    """
    path = path or DATA_DIR / "movies.dat"

    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        encoding="latin-1",       # Xử lý ký tự đặc biệt trong tên phim
        names=["movie_id", "title", "genres"],
        dtype={"movie_id": np.int32},
    )

    # Chuẩn hóa: bỏ khoảng trắng thừa
    df["title"]  = df["title"].str.strip()
    df["genres"] = df["genres"].str.strip()

    # Kiểm tra missing
    n_missing = df.isnull().sum().sum()
    if n_missing > 0:
        print(f"[WARN] movies.dat có {n_missing} missing values — đang drop...")
        df.dropna(inplace=True)
    else:
        print(f"[OK]   movies.dat   — {len(df):,} phim, 0 missing values.")

    # Trích xuất năm phát hành từ tiêu đề "(Year)"
    df["year"] = (
        df["title"]
        .str.extract(r"\((\d{4})\)$")
        .astype("Int16")           # Nullable integer (hỗ trợ NaN)
    )

    return df.reset_index(drop=True)


def load_users(path: Path | None = None) -> pd.DataFrame:
    """
    Load file users.dat.

    Schema  : UserID :: Gender :: Age :: Occupation :: Zip-code
    Age     : Giá trị mã hóa (1, 18, 25, 35, 45, 50, 56)
    Returns : DataFrame với các cột [user_id, gender, age, occupation, zip_code]
    """
    path = path or DATA_DIR / "users.dat"

    # Mapping tuổi từ mã → trung điểm khoảng tuổi thực
    AGE_MAP = {
        1:  15,   # Under 18  → lấy đại diện = 15
        18: 21,   # 18–24     → 21
        25: 30,   # 25–34     → 30
        35: 40,   # 35–44     → 40
        45: 47,   # 45–49     → 47
        50: 52,   # 50–55     → 52
        56: 60,   # 56+       → 60
    }

    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        names=["user_id", "gender", "age", "occupation", "zip_code"],
        dtype={
            "user_id":    np.int32,
            "age":        np.int8,
            "occupation": np.int8,
        },
    )

    # Kiểm tra missing
    n_missing = df.isnull().sum().sum()
    if n_missing > 0:
        print(f"[WARN] users.dat có {n_missing} missing values — đang drop...")
        df.dropna(inplace=True)
    else:
        print(f"[OK]   users.dat    — {len(df):,} users, 0 missing values.")

    # Thêm cột age_midpoint để dễ phân tích (giữ nguyên cột 'age' gốc)
    df["age_midpoint"] = df["age"].map(AGE_MAP).astype(np.float32)

    return df.reset_index(drop=True)


def load_all(data_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load và trả về đồng thời 3 DataFrame: (ratings, movies, users).

    Parameters
    ----------
    data_dir : Path, optional
        Đường dẫn tới thư mục chứa các file .dat.
        Nếu None, dùng DATA_DIR mặc định.

    Returns
    -------
    ratings : pd.DataFrame
    movies  : pd.DataFrame
    users   : pd.DataFrame
    """
    global DATA_DIR
    if data_dir is not None:
        DATA_DIR = Path(data_dir)

    print("=" * 50)
    print("  Loading MovieLens 1M Dataset")
    print("=" * 50)

    ratings = load_ratings()
    movies  = load_movies()
    users   = load_users()

    print("-" * 50)
    print(f"  Tổng ratings   : {len(ratings):>10,}")
    print(f"  Tổng users     : {len(users):>10,}")
    print(f"  Tổng movies    : {len(movies):>10,}")
    print("=" * 50)

    return ratings, movies, users


# ──────────────────────────────────────────────
#  Chạy thử trực tiếp
# ──────────────────────────────────────────────
if __name__ == "__main__":
    ratings, movies, users = load_all()
    print("\nSample ratings:\n", ratings.head(3))
    print("\nSample movies:\n",  movies.head(3))
    print("\nSample users:\n",   users.head(3))
    print("\nDtypes ratings:\n", ratings.dtypes)
