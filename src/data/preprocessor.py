import pandas as pd
from typing import Tuple

class DataPreprocessor:
    """
    Module tiền xử lý dữ liệu:
    1. Mapping ID từ Raw sang Index (0 đến N-1) cho Matrix Factorization.
    2. Chia tách Train/Test.
    """
    def __init__(self):
        # Dictionaries hỗ trợ lookup O(1)
        self.user2idx = {}
        self.idx2user = {}
        self.movie2idx = {}
        self.idx2movie = {}

    def map_ids(self, ratings: pd.DataFrame) -> pd.DataFrame:
        """
        Chuyển đổi user_id và movie_id gốc thành chỉ mục (index) liên tục từ 0.
        Giải thích: Thuật toán như SVD/Embedding dùng array/tensor, yêu cầu index liên tục.
        Nếu dùng ID gốc (vd: 10, 50, 200) sẽ tạo ra ma trận với nhiều dòng thừa thãi, tốn bộ nhớ.
        """
        print("System log: Action in progress")
        unique_users = ratings['user_id'].unique()
        unique_movies = ratings['movie_id'].unique()

        # Tạo Dictionary
        self.user2idx = {u: i for i, u in enumerate(unique_users)}
        self.idx2user = {i: u for i, u in enumerate(unique_users)}
        
        self.movie2idx = {m: i for i, m in enumerate(unique_movies)}
        self.idx2movie = {i: m for i, m in enumerate(unique_movies)}

        # Dùng hàm .map() của Pandas (Vectorized) nhanh hơn gấp ngàn lần so với vòng lặp
        mapped_ratings = ratings.copy()
        mapped_ratings['user_idx'] = mapped_ratings['user_id'].map(self.user2idx)
        mapped_ratings['movie_idx'] = mapped_ratings['movie_id'].map(self.movie2idx)
        
        return mapped_ratings

    def time_based_split(self, ratings: pd.DataFrame, test_ratio: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Chia tập Train/Test theo dòng thời gian (Timestamp).
        Giải thích: Tránh "Data Leakage" (dùng tương lai đoán quá khứ). 
        Những rating mới nhất sẽ được dùng làm Test set.
        """
        print(f"Splitting Train/Test by Timestamp (Test ratio: {test_ratio * 100}%)...")
        # Sắp xếp toàn bộ dữ liệu theo thời gian thực
        ratings_sorted = ratings.sort_values('timestamp')
        
        # Cắt lấy vị trí chia
        split_idx = int(len(ratings_sorted) * (1 - test_ratio))
        
        train_df = ratings_sorted.iloc[:split_idx].copy()
        test_df = ratings_sorted.iloc[split_idx:].copy()
        
        return train_df, test_df
