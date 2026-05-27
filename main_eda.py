import sys
from pathlib import Path

# Thêm thư mục gốc vào đường dẫn hệ thống để import module dễ dàng
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from config.settings import RATINGS_PATH, MOVIES_PATH, USERS_PATH, EDA_OUTPUT_DIR
from src.data.data_loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.features.feature_engineering import FeatureEngineer
from src.eda.visualizer import Visualizer

def main():
    print("Bat dau qua trinh Exploratory Data Analysis (EDA)...")
    
    # 1. Khởi tạo và Load dữ liệu
    loader = DataLoader(RATINGS_PATH, MOVIES_PATH, USERS_PATH)
    ratings = loader.load_ratings()
    movies = loader.load_movies()
    users = loader.load_users()
    
    # 2. In ra Sparsity
    Visualizer.print_sparsity(ratings)
    
    # 3. Tiền xử lý (Ví dụ minh họa việc chia tách và mapping)
    preprocessor = DataPreprocessor()
    ratings_mapped = preprocessor.map_ids(ratings)
    train_df, test_df = preprocessor.time_based_split(ratings_mapped, test_ratio=0.2)
    print(f"Số dòng Train: {len(train_df):,}, Số dòng Test: {len(test_df):,}\n")
    
    # 4. Feature Engineering
    movies_processed = FeatureEngineer.process_movies(movies)
    users_processed = FeatureEngineer.process_users(users)
    
    # 5. Sinh biểu đồ bằng Visualizer
    visualizer = Visualizer(EDA_OUTPUT_DIR)
    visualizer.plot_rating_distribution(ratings)
    visualizer.plot_long_tail(ratings)
    visualizer.plot_activity(ratings)
    visualizer.plot_genre_analysis(movies_processed)
    
    print(f"\nDa hoan tat! Cac bieu do EDA da duoc luu tai: {EDA_OUTPUT_DIR}")

if __name__ == "__main__":
    main()
