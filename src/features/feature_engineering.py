import pandas as pd
import warnings
# Bỏ qua warning của pandas khi concat
warnings.simplefilter(action='ignore', category=FutureWarning)

class FeatureEngineer:
    """
    Module phụ trách biến đổi đặc trưng (Feature Engineering):
    - Multi-hot encoding cho thể loại phim (Genres).
    - Chuẩn hóa (Normalization) cho thông tin User.
    """
    
    @staticmethod
    def process_movies(movies: pd.DataFrame) -> pd.DataFrame:
        """
        Xử lý cột 'genres'. Các thể loại được ngăn cách bởi dấu '|'.
        Hàm này sẽ tạo ra ma trận Multi-hot encoding (Mỗi thể loại là 1 cột chứa 0 hoặc 1).
        Giải thích: Rất quan trọng cho các mô hình Content-Based hoặc Hybrid.
        """
        print("System log: Action in progress")
        df = movies.copy()
        
        # Hàm get_dummies của str trong Pandas thực hiện vectorization tạo ma trận nhị phân
        genres_dummies = df['genres'].str.get_dummies(sep='|')
        
        # Nối lại vào DataFrame gốc
        df = pd.concat([df, genres_dummies], axis=1)
        return df

    @staticmethod
    def process_users(users: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn hóa thông tin User (Gender, Age, Occupation).
        Giải thích: Neural Networks hoặc các thuật toán tính khoảng cách (KNN) 
        rất nhạy cảm với các biến có thang đo khác nhau.
        """
        print("System log: Action in progress")
        df = users.copy()
        
        # 1. Binary Encoding cho Giới tính
        df['gender_mapped'] = df['gender'].map({'M': 1, 'F': 0})
        
        # 2. Min-Max Scaling cho Tuổi
        min_age = df['age'].min()
        max_age = df['age'].max()
        df['age_norm'] = (df['age'] - min_age) / (max_age - min_age)
        
        # 3. One-hot Encoding cho Nghề nghiệp (Occupation)
        occupation_dummies = pd.get_dummies(df['occupation'], prefix='occ')
        df = pd.concat([df, occupation_dummies], axis=1)
        
        return df
