import pandas as pd
from pathlib import Path
import logging

class DataLoader:
    """
    Module phụ trách đọc dữ liệu từ các file .dat của MovieLens.
    Sử dụng Pandas và Pathlib để đảm bảo tính an toàn và tốc độ.
    """
    def __init__(self, ratings_path: Path, movies_path: Path, users_path: Path):
        """
        Khởi tạo DataLoader với các đường dẫn được tiêm vào (Dependency Injection).
        """
        self.ratings_path = ratings_path
        self.movies_path = movies_path
        self.users_path = users_path

    def load_ratings(self) -> pd.DataFrame:
        """Đọc file ratings.dat"""
        print("Loading ratings data...")
        return pd.read_csv(
            self.ratings_path,
            sep='::',
            engine='python',
            names=['user_id', 'movie_id', 'rating', 'timestamp'],
            encoding='latin-1'
        )

    def load_movies(self) -> pd.DataFrame:
        """Đọc file movies.dat"""
        print("System log: Action in progress")
        return pd.read_csv(
            self.movies_path,
            sep='::',
            engine='python',
            names=['movie_id', 'title', 'genres'],
            encoding='latin-1'
        )

    def load_users(self) -> pd.DataFrame:
        """Đọc file users.dat"""
        print("System log: Action in progress")
        return pd.read_csv(
            self.users_path,
            sep='::',
            engine='python',
            names=['user_id', 'gender', 'age', 'occupation', 'zip_code'],
            encoding='latin-1'
        )
