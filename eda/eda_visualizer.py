"""
eda_visualizer.py
=================
Module thực hiện Exploratory Data Analysis (EDA) với Matplotlib/Seaborn.

Các biểu đồ bao gồm:
1. Phân phối Ratings (1-5 sao).
2. Phân phối số lượng rating trên mỗi user & movie (Long-tail).
3. Sở thích thể loại (Genres) theo demographic (Tuổi, Giới tính).

Tác giả  : Senior AI Engineer
Mục đích : Đồ án tốt nghiệp — Movie Recommender System
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path


# Cấu hình thư mục lưu ảnh
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Thiết lập style mặc định cho Seaborn
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)


def plot_rating_distribution(ratings: pd.DataFrame):
    """Vẽ biểu đồ phân phối điểm đánh giá (1-5 sao)."""
    plt.figure()
    ax = sns.countplot(x="rating", data=ratings, palette="viridis")
    plt.title("Phân phối điểm đánh giá (Ratings Distribution)", fontsize=14)
    plt.xlabel("Rating (Stars)", fontsize=12)
    plt.ylabel("Số lượng", fontsize=12)
    
    # Thêm text số lượng trên cột
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height()):,}", 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha="center", va="bottom", fontsize=10)
    
    out_path = OUTPUT_DIR / "rating_distribution.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[EDA] Đã lưu biểu đồ: {out_path.name}")


def plot_long_tail(ratings: pd.DataFrame):
    """
    Vẽ 2 biểu đồ Long-tail:
    1. Số lượng rating theo từng Movie (sắp xếp giảm dần).
    2. Số lượng rating theo từng User (sắp xếp giảm dần).
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # --- 1. Long-tail Movies ---
    movie_counts = ratings["movie_id"].value_counts().values
    axes[0].plot(movie_counts, color="blue", linewidth=2)
    axes[0].fill_between(range(len(movie_counts)), movie_counts, color="blue", alpha=0.3)
    axes[0].set_title("Phân phối số lượng rating theo Phim (Long-tail)", fontsize=14)
    axes[0].set_xlabel("Phim (Được sắp xếp theo độ phổ biến)", fontsize=12)
    axes[0].set_ylabel("Số lượng Ratings", fontsize=12)

    # --- 2. Long-tail Users ---
    user_counts = ratings["user_id"].value_counts().values
    axes[1].plot(user_counts, color="green", linewidth=2)
    axes[1].fill_between(range(len(user_counts)), user_counts, color="green", alpha=0.3)
    axes[1].set_title("Phân phối số lượng rating theo User", fontsize=14)
    axes[1].set_xlabel("User (Được sắp xếp theo mức độ active)", fontsize=12)
    axes[1].set_ylabel("Số lượng Ratings", fontsize=12)

    out_path = OUTPUT_DIR / "long_tail.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[EDA] Đã lưu biểu đồ: {out_path.name}")


def plot_genre_preferences(ratings_fe: pd.DataFrame, movies_fe: pd.DataFrame, users_fe: pd.DataFrame):
    """
    Vẽ biểu đồ thể hiện sở thích thể loại phim theo giới tính.
    Cần join 3 bảng lại với nhau trước khi phân tích.
    """
    # Lấy danh sách cột genre
    genre_cols = [c for c in movies_fe.columns if c.startswith("genre_")]
    
    # Merge dữ liệu
    df_merged = ratings_fe[["user_id", "movie_id", "rating"]].merge(
        users_fe[["user_id", "gender"]], on="user_id"
    ).merge(
        movies_fe[["movie_id"] + genre_cols], on="movie_id"
    )

    # Tính rating trung bình cho mỗi thể loại theo giới tính
    genre_gender_ratings = []
    
    for g_col in genre_cols:
        genre_name = g_col.replace("genre_", "")
        # Lọc những dòng có phim thuộc thể loại này
        subset = df_merged[df_merged[g_col] == 1]
        if not subset.empty:
            avg_ratings = subset.groupby("gender")["rating"].mean()
            genre_gender_ratings.append({
                "Genre": genre_name,
                "F (Female)": avg_ratings.get("F", 0),
                "M (Male)": avg_ratings.get("M", 0)
            })

    df_genre = pd.DataFrame(genre_gender_ratings).set_index("Genre")
    df_genre = df_genre.sort_values("F (Female)", ascending=True) # Sắp xếp để vẽ đẹp hơn
    
    # Vẽ biểu đồ Horizontal Bar Chart
    ax = df_genre.plot(kind="barh", figsize=(12, 8), color=["#FF9999", "#66B2FF"])
    plt.title("Rating Trung Bình Của Các Thể Loại Theo Giới Tính", fontsize=16)
    plt.xlabel("Rating Trung Bình", fontsize=12)
    plt.ylabel("Thể Loại (Genre)", fontsize=12)
    plt.legend(title="Gender")
    plt.xlim(2.5, 4.5) # Zoom in vào khoảng điểm thực tế
    
    out_path = OUTPUT_DIR / "genre_preferences.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"[EDA] Đã lưu biểu đồ: {out_path.name}")


def calculate_sparsity(ratings: pd.DataFrame, movies: pd.DataFrame, users: pd.DataFrame) -> float:
    """Tính chỉ số Sparsity của User-Item matrix."""
    n_users = users["user_id"].nunique()
    n_movies = movies["movie_id"].nunique()
    n_ratings = len(ratings)
    
    total_possible = n_users * n_movies
    sparsity = (1.0 - (n_ratings / total_possible)) * 100
    
    print("-" * 50)
    print("  User-Item Matrix Sparsity")
    print("-" * 50)
    print(f"Tổng Users         : {n_users:,}")
    print(f"Tổng Movies        : {n_movies:,}")
    print(f"Số ô có dữ liệu    : {n_ratings:,}")
    print(f"Tổng số ô          : {total_possible:,}")
    print(f"Sparsity           : {sparsity:.2f}%")
    print("-" * 50)
    
    return sparsity


def run_eda(ratings: pd.DataFrame, movies: pd.DataFrame, users: pd.DataFrame, 
            ratings_fe: pd.DataFrame, movies_fe: pd.DataFrame, users_fe: pd.DataFrame):
    """Hàm chạy toàn bộ pipeline EDA."""
    print("\n" + "=" * 50)
    print("  Bắt đầu chạy EDA...")
    print("=" * 50)
    
    plot_rating_distribution(ratings)
    plot_long_tail(ratings)
    plot_genre_preferences(ratings_fe, movies_fe, users_fe)
    calculate_sparsity(ratings, movies, users)
    
    print("\n[EDA] Hoàn tất! Các biểu đồ đã được lưu trong folder 'output/eda'.")
