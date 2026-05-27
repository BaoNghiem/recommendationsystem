"""
matrix_builder.py
=================
Module phụ trách tạo Sparse Matrix và User/Movie ID mapping.

Việc chuyển dữ liệu sang Scipy Sparse Matrix (CSR format) giúp:
1. Giải quyết lỗi Memory Error khi dùng pivot_table trên dữ liệu lớn.
2. Tối ưu O(1) lookup thông qua hệ thống index mapping.

Tác giả  : Senior AI Engineer
Mục đích : Đồ án tốt nghiệp — Movie Recommender System
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
import pickle
from pathlib import Path


# Cấu hình thư mục lưu mapping và matrix
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "matrix"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_sparse_matrix(ratings: pd.DataFrame) -> tuple[csr_matrix, dict, dict]:
    """
    Chuyển ratings DataFrame thành Sparse Matrix (CSR format).
    Đồng thời tạo dictionary mapping giữa ID gốc và Index ma trận (0 to N-1).

    Parameters
    ----------
    ratings : pd.DataFrame
        Cần có các cột ['user_id', 'movie_id', 'rating']

    Returns
    -------
    sparse_matrix : scipy.sparse.csr_matrix
        Ma trận kích thước (n_users, n_movies)
    user_mapping  : dict
        Mapping {user_id_gốc: index_mới}
    movie_mapping : dict
        Mapping {movie_id_gốc: index_mới}
    """
    print("\n" + "=" * 50)
    print("  Bắt đầu tạo Sparse Matrix (CSR)...")
    print("=" * 50)

    # 1. Tạo danh sách ID duy nhất
    unique_users = np.unique(ratings["user_id"])
    unique_movies = np.unique(ratings["movie_id"])

    n_users = len(unique_users)
    n_movies = len(unique_movies)

    # 2. Tạo Mapping Dictionaries (Original ID -> Matrix Index)
    user_mapping = {uid: idx for idx, uid in enumerate(unique_users)}
    movie_mapping = {mid: idx for idx, mid in enumerate(unique_movies)}

    # 3. Chuyển đổi cột ID trong dataframe sang Index
    user_indices = ratings["user_id"].map(user_mapping).values
    movie_indices = ratings["movie_id"].map(movie_mapping).values
    rating_values = ratings["rating"].values

    # 4. Xây dựng CSR Matrix
    # csr_matrix((data, (row_ind, col_ind)), [shape=(M, N)])
    sparse_matrix = csr_matrix(
        (rating_values, (user_indices, movie_indices)),
        shape=(n_users, n_movies),
        dtype=np.float32
    )

    print(f"[OK] Đã tạo Sparse Matrix kích thước: {sparse_matrix.shape}")
    print(f"     - Số phần tử khác 0 (NNZ)  : {sparse_matrix.nnz:,}")
    print(f"     - Dung lượng bộ nhớ (CSR)  : {sparse_matrix.data.nbytes / 1e6:.2f} MB")
    
    return sparse_matrix, user_mapping, movie_mapping


def save_matrix_and_mappings(sparse_matrix: csr_matrix, user_mapping: dict, movie_mapping: dict):
    """Lưu CSR matrix và mapping dicts xuống file pickle để dùng ở các bước sau."""
    matrix_path = OUTPUT_DIR / "user_item_csr.pkl"
    mappings_path = OUTPUT_DIR / "id_mappings.pkl"

    with open(matrix_path, "wb") as f:
        pickle.dump(sparse_matrix, f)

    with open(mappings_path, "wb") as f:
        pickle.dump({
            "user_mapping": user_mapping,
            "movie_mapping": movie_mapping
        }, f)

    print(f"[OK] Đã lưu matrix tại: {matrix_path}")
    print(f"[OK] Đã lưu mappings tại: {mappings_path}")
    print("=" * 50)


# ──────────────────────────────────────────────
#  Chạy thử trực tiếp
# ──────────────────────────────────────────────
if __name__ == "__main__":
    from data_loader import load_ratings
    
    ratings_df = load_ratings()
    mat, u_map, m_map = build_sparse_matrix(ratings_df)
    save_matrix_and_mappings(mat, u_map, m_map)
