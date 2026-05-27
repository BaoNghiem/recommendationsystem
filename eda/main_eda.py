"""
main_eda.py
===========
Script chính chạy toàn bộ quy trình Exploratory Data Analysis (EDA) 
& Advanced Preprocessing cho đồ án Movie Recommender System.

Các bước thực hiện:
1. Load Data (Ratings, Movies, Users)
2. Feature Engineering (Genres, Demographics, Time)
3. EDA Visualizations (Lưu ảnh vào thư mục output/eda/)
4. Xây dựng Sparse Matrix (CSR) & lưu trữ (output/matrix/)

Tác giả: Senior AI Engineer
"""

import sys
from pathlib import Path

# Đảm bảo Python hiểu các module trong cùng thư mục
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from data_loader import load_all
from feature_engineering import run_feature_engineering
from eda_visualizer import run_eda
from matrix_builder import build_sparse_matrix, save_matrix_and_mappings


def main():
    print("=" * 60)
    print("  GIAI ĐOẠN 1: EDA & ADVANCED PREPROCESSING BẮT ĐẦU")
    print("=" * 60)

    # 1. Load Data
    print("\n[BƯỚC 1] Data Loading & Cleaning...")
    ratings, movies, users = load_all()

    # 2. Feature Engineering
    print("\n[BƯỚC 2] Feature Engineering...")
    ratings_fe, movies_fe, users_fe = run_feature_engineering(ratings, movies, users)

    # 3. Exploratory Data Analysis (EDA)
    print("\n[BƯỚC 3] Data Visualization (EDA)...")
    run_eda(ratings, movies, users, ratings_fe, movies_fe, users_fe)

    # 4. Matrix Building
    print("\n[BƯỚC 4] Xây dựng Scipy Sparse Matrix...")
    sparse_matrix, user_mapping, movie_mapping = build_sparse_matrix(ratings)
    save_matrix_and_mappings(sparse_matrix, user_mapping, movie_mapping)

    print("\n" + "=" * 60)
    print("  HOÀN TẤT GIAI ĐOẠN 1!")
    print("  - Biểu đồ đã lưu tại    : output/eda/")
    print("  - CSR Matrix đã lưu tại : output/matrix/")
    print("=" * 60)


if __name__ == "__main__":
    main()
