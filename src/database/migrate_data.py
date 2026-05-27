import sys
from pathlib import Path
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values

# Thiet lap path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db_config import DatabaseConnector
from config.settings import RATINGS_PATH, MOVIES_PATH, USERS_PATH
from src.data.data_loader import DataLoader
from src.features.feature_engineering import FeatureEngineer

def migrate_all_data():
    """
    Script nạp dữ liệu từ MovieLens 1M vào PostgreSQL.
    Su dung ky thuat Bulk Insert (execute_values) cho hieu nang cao nhat.
    """
    
    # 1. Kiem tra ket noi truoc khi lam viec
    if not DatabaseConnector.test_connection():
        return

    # 2. Doc du lieu tu file .dat
    print("Dang doc du lieu tu file .dat (MovieLens 1M)...")
    loader = DataLoader(RATINGS_PATH, MOVIES_PATH, USERS_PATH)
    df_ratings = loader.load_ratings()
    df_movies = loader.load_movies()
    df_users = loader.load_users()

    # 3. Xu ly Movie Features (One-hot encoding genres)
    print("Dang xu ly Feature Engineering cho Movies...")
    df_movies_proc = FeatureEngineer.process_movies(df_movies)
    # Chuan hoa ten cot genre sang viet thuong de khop voi SQL Schema
    genre_cols = ['action', 'adventure', 'animation', 'childrens', 'comedy', 'crime', 
                  'documentary', 'drama', 'fantasy', 'film_noir', 'horror', 'musical', 
                  'mystery', 'romance', 'sci_fi', 'thriller', 'war', 'western']
    # Lưu ý: Sửa tên cột DataFrame cho khớp (vd: 'Action' -> 'action')
    df_movies_proc.columns = [c.lower().replace('-', '_').replace("'", "") for c in df_movies_proc.columns]

    conn = DatabaseConnector.get_connection()
    cur = conn.cursor()

    try:
        # 4. Xoa du lieu cu (Truncate) de tranh loi Duplicate
        print("Dang lam sach (Truncate) cac bang cu...")
        cur.execute("TRUNCATE ratings, users, movies CASCADE;")

        # 5. Migration Movies
        print("Dang nap du lieu Movies (kem Genre features)...")
        movie_cols = ['movie_id', 'title', 'genres'] + genre_cols
        movie_data = df_movies_proc[movie_cols].values.tolist()
        execute_values(cur, f"INSERT INTO movies ({', '.join(['movie_id', 'title', 'genres_orig'] + genre_cols)}) VALUES %s", movie_data)

        # 6. Migration Users
        print("Dang nap du lieu Users...")
        user_data = df_users[['user_id', 'gender', 'age', 'occupation']].values.tolist()
        execute_values(cur, "INSERT INTO users (user_id, gender, age, occupation) VALUES %s", user_data)

        # 7. Migration Ratings (Day la buoc nang nhat - 1 trieu dong)
        print("Dang nap 1 TRIEU dong Ratings (Bulk Insert)...")
        rating_data = df_ratings[['user_id', 'movie_id', 'rating', 'timestamp']].values.tolist()
        # Chia nho batch (vi du 100k moi lan) de tranh tran bo nho neu can, 
        # nhung execute_values thuong handle tot 1M.
        execute_values(cur, "INSERT INTO ratings (user_id, movie_id, rating, timestamp) VALUES %s", rating_data)

        conn.commit()
        print("\n" + "="*40)
        print("MIGRATION HOAN TAT XUAT SAC!")
        
        # 8. Verify - Doi soat du lieu
        print("--- KET QUA DOI SOAT (VERIFICATION) ---")
        cur.execute("SELECT count(*) FROM movies")
        print(f"- So luong Phim: {cur.fetchone()[0]:,}")
        cur.execute("SELECT count(*) FROM users")
        print(f"- So luong User: {cur.fetchone()[0]:,}")
        cur.execute("SELECT count(*) FROM ratings")
        print(f"- So luong Rating: {cur.fetchone()[0]:,}")
        print("="*40)

    except Exception as e:
        print(f"LOI TRONG QUA TRINH MIGRATION: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_all_data()
