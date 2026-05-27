"""
feature_engineering.py
======================
Module thực hiện toàn bộ Feature Engineering cho 3 bảng dữ liệu:

  • Movies  : One-hot encoding genres (18 thể loại)
  • Users   : Encode gender, normalize age & occupation
  • Ratings : Trích xuất đặc trưng thời gian từ timestamp
              (giờ trong ngày, ngày trong tuần, tháng)

Tác giả  : Senior AI Engineer
Mục đích : Đồ án tốt nghiệp — Movie Recommender System
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


# ─────────────────────────────────────────────────
#  1. MOVIES — One-hot Encoding cho Genres
# ─────────────────────────────────────────────────

# Danh sách tất cả 18 thể loại hợp lệ theo chuẩn MovieLens 1M
ALL_GENRES: list[str] = [
    "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir",
    "Horror", "Musical", "Mystery", "Romance", "Sci-Fi",
    "Thriller", "War", "Western",
]


def encode_genres(movies: pd.DataFrame) -> pd.DataFrame:
    """
    Thêm 18 cột one-hot cho genres vào DataFrame movies.

    Ví dụ: "Action|Adventure|Sci-Fi" → Action=1, Adventure=1, Sci-Fi=1, ...=0

    Parameters
    ----------
    movies : pd.DataFrame  (output từ data_loader.load_movies)

    Returns
    -------
    pd.DataFrame có thêm 18 cột genre (dtype int8 để tiết kiệm RAM)
    """
    df = movies.copy()

    for genre in ALL_GENRES:
        col_name = "genre_" + genre.replace('-', '_').replace("'", "").replace(' ', '_')
        # str.contains dùng regex=False để tránh escape ký tự đặc biệt
        df[col_name] = df["genres"].str.contains(genre, regex=False).astype(np.int8)

    # Đếm số thể loại mỗi phim (feature bổ sung hữu ích)
    genre_cols = [c for c in df.columns if c.startswith("genre_")]
    df["n_genres"] = df[genre_cols].sum(axis=1).astype(np.int8)

    print(f"[OK]   encode_genres  — Thêm {len(genre_cols)} cột genre "
          f"+ cột 'n_genres' (trung bình {df['n_genres'].mean():.1f} thể loại/phim).")
    return df


# ─────────────────────────────────────────────────
#  2. USERS — Encode Gender + Normalize Age & Occupation
# ─────────────────────────────────────────────────

# Nhãn occupation để dễ đọc (không dùng trong encoding nhưng hữu ích cho EDA)
OCCUPATION_LABELS: dict[int, str] = {
    0:  "other",            1:  "academic/educator",  2:  "artist",
    3:  "clerical/admin",   4:  "college/grad student", 5: "customer service",
    6:  "doctor",           7:  "executive/managerial", 8: "farmer",
    9:  "homemaker",        10: "K-12 student",         11: "lawyer",
    12: "programmer",       13: "retired",              14: "sales/marketing",
    15: "scientist",        16: "self-employed",        17: "technician/engineer",
    18: "tradesman",        19: "unemployed",           20: "writer",
}


def encode_users(users: pd.DataFrame) -> pd.DataFrame:
    """
    Feature Engineering cho bảng users:

    1. gender_encoded  : M → 0, F → 1
    2. age_norm        : age_midpoint chuẩn hóa về [0, 1] bằng MinMaxScaler
    3. occupation_norm : occupation (0–20) chuẩn hóa về [0, 1]
    4. occupation_label: tên nghề nghiệp dạng string (để EDA)

    Parameters
    ----------
    users : pd.DataFrame  (output từ data_loader.load_users)

    Returns
    -------
    pd.DataFrame với các cột mới đã được encode/normalize.
    """
    df = users.copy()

    # --- 2a. Encode Gender ---
    df["gender_encoded"] = (df["gender"] == "F").astype(np.int8)
    # M=0, F=1

    # --- 2b. Normalize Age (dùng age_midpoint đã tạo ở data_loader) ---
    scaler_age = MinMaxScaler()
    df["age_norm"] = scaler_age.fit_transform(
        df["age_midpoint"].values.reshape(-1, 1)
    ).astype(np.float32)

    # --- 2c. Normalize Occupation ---
    scaler_occ = MinMaxScaler()
    df["occupation_norm"] = scaler_occ.fit_transform(
        df["occupation"].values.reshape(-1, 1)
    ).astype(np.float32)

    # --- 2d. Thêm label dạng string cho EDA ---
    df["occupation_label"] = df["occupation"].map(OCCUPATION_LABELS)

    # --- 2e. Nhóm tuổi dạng string để vẽ biểu đồ ---
    age_group_map = {
        1:  "<18",
        18: "18–24",
        25: "25–34",
        35: "35–44",
        45: "45–49",
        50: "50–55",
        56: "56+",
    }
    df["age_group"] = df["age"].map(age_group_map)

    print(f"[OK]   encode_users   — gender_encoded, age_norm, occupation_norm đã được thêm.")
    return df


# ─────────────────────────────────────────────────
#  3. RATINGS — Trích xuất đặc trưng thời gian
# ─────────────────────────────────────────────────

def extract_time_features(ratings: pd.DataFrame) -> pd.DataFrame:
    """
    Trích xuất đặc trưng thời gian từ cột 'timestamp' (Unix epoch).

    Các cột được thêm:
      • datetime       : timestamp dạng datetime (UTC)
      • hour_of_day    : 0–23 — phân tích thói quen xem phim ban ngày/đêm
      • day_of_week    : 0=Monday, 6=Sunday — cuối tuần vs ngày thường
      • month          : 1–12 — xu hướng theo mùa
      • is_weekend     : 1 nếu Thứ 7 hoặc Chủ nhật, 0 ngược lại
      • time_of_day    : 'Morning' / 'Afternoon' / 'Evening' / 'Night'

    Parameters
    ----------
    ratings : pd.DataFrame  (output từ data_loader.load_ratings)

    Returns
    -------
    pd.DataFrame với các cột thời gian bổ sung.
    """
    df = ratings.copy()

    # Chuyển Unix timestamp → datetime
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

    # Các đặc trưng số
    df["hour_of_day"]  = df["datetime"].dt.hour.astype(np.int8)
    df["day_of_week"]  = df["datetime"].dt.dayofweek.astype(np.int8)   # 0=Mon
    df["month"]        = df["datetime"].dt.month.astype(np.int8)
    df["is_weekend"]   = (df["day_of_week"] >= 5).astype(np.int8)

    # Phân loại khung giờ trong ngày
    def categorize_hour(h: int) -> str:
        if  6 <= h < 12: return "Morning"
        if 12 <= h < 18: return "Afternoon"
        if 18 <= h < 22: return "Evening"
        return "Night"   # 22–5h sáng

    df["time_of_day"] = df["hour_of_day"].map(categorize_hour)

    print(f"[OK]   extract_time   — Thêm: hour_of_day, day_of_week, month, "
          f"is_weekend, time_of_day.")
    print(f"         Khoảng thời gian: "
          f"{df['datetime'].min().date()} → {df['datetime'].max().date()}")

    # Có thể drop cột 'timestamp' nếu không cần nữa (comment out nếu cần giữ)
    # df.drop(columns=["timestamp"], inplace=True)

    return df


# ─────────────────────────────────────────────────
#  4. PIPELINE tổng hợp
# ─────────────────────────────────────────────────

def run_feature_engineering(
    ratings: pd.DataFrame,
    movies:  pd.DataFrame,
    users:   pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chạy toàn bộ feature engineering pipeline và trả về 3 DataFrame đã được xử lý.

    Returns
    -------
    ratings_fe, movies_fe, users_fe
    """
    print("\n" + "=" * 50)
    print("  Feature Engineering Pipeline")
    print("=" * 50)

    movies_fe  = encode_genres(movies)
    users_fe   = encode_users(users)
    ratings_fe = extract_time_features(ratings)

    print("=" * 50)
    print("  Feature Engineering hoàn tất!")
    print(f"  ratings shape : {ratings_fe.shape}")
    print(f"  movies shape  : {movies_fe.shape}")
    print(f"  users shape   : {users_fe.shape}")
    print("=" * 50)

    return ratings_fe, movies_fe, users_fe


# ──────────────────────────────────────────────
#  Chạy thử trực tiếp
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from data_loader import load_all

    ratings, movies, users = load_all()
    ratings_fe, movies_fe, users_fe = run_feature_engineering(ratings, movies, users)

    # Xem thử các cột genre
    genre_cols = [c for c in movies_fe.columns if c.startswith("genre_")]
    print("\nGenre columns sample:\n", movies_fe[["title"] + genre_cols[:5]].head(3))

    # Xem thử users đã encode
    print("\nUsers encoded sample:\n",
          users_fe[["user_id", "gender", "gender_encoded", "age_group",
                    "age_norm", "occupation_label"]].head(3))

    # Xem thử time features
    print("\nRatings time features sample:\n",
          ratings_fe[["user_id", "rating", "hour_of_day",
                       "day_of_week", "is_weekend", "time_of_day"]].head(3))
