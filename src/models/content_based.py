import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedModel:
    """
    Gợi ý dựa trên đặc trưng nội dung (Genres).
    Sử dụng Cosine Similarity để tìm các item tương đồng.
    """
    def __init__(self):
        self.movie_sim_matrix = None
        self.movie_idx_to_pos = None 
        self.pos_to_movie_idx = None
        self.genre_matrix = None

    def fit(self, movies_processed):
        """
        movies_processed: DataFrame đã qua Feature Engineering (Multi-hot genres).
        """
        print("Dang tinh toan ma tran tuong dong Cosine (Content-Based)...")
        
        # 1. Xác định các cột thể loại
        exclude = ['movie_id', 'title', 'genres', 'movie_idx']
        genre_cols = [c for c in movies_processed.columns if c not in exclude]
        
        # 2. Lấy ma trận genre nhị phân
        self.genre_matrix = movies_processed[genre_cols].values
        
        # 3. Tính Cosine Similarity (Kích thước: N_movies x N_movies)
        self.movie_sim_matrix = cosine_similarity(self.genre_matrix)
        
        # 4. Tạo bản đồ tra cứu
        self.movie_idx_to_pos = {idx: i for i, idx in enumerate(movies_processed['movie_idx'])}
        self.pos_to_movie_idx = {i: idx for i, idx in enumerate(movies_processed['movie_idx'])}
        
        print(f"Hoan tat tinh toan cho {len(movies_processed)} bo phim.")

    def get_content_score(self, movie_idx, user_history_indices):
        """
        Tính điểm tương đồng của một phim so với lịch sử các phim user đã xem.
        """
        if movie_idx not in self.movie_idx_to_pos:
            return 0
            
        target_pos = self.movie_idx_to_pos[movie_idx]
        
        # Lấy lịch sử vị trí trong ma trận sim
        history_positions = [self.movie_idx_to_pos[idx] for idx in user_history_indices if idx in self.movie_idx_to_pos]
        
        if not history_positions:
            return 0
            
        # Điểm tương đồng = Trung bình cộng độ tương đồng với các phim trong lịch sử
        sim_scores = self.movie_sim_matrix[target_pos][history_positions]
        return np.mean(sim_scores)
