import sys
from pathlib import Path
import time
import shutil
import pickle

# Thiết lập đường dẫn hệ thống
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from config.settings import RATINGS_PATH, MOVIES_PATH, USERS_PATH, MODEL_OUTPUT_DIR
from src.data.data_loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.models.funk_svd import FunkSVDModel
from src.evaluation.evaluator import Evaluator


def atomic_save(obj, target_path, save_func=None):
    """
    Ghi file an toan: ghi vao file .tmp truoc, roi rename (atomic).
    Neu server restart giua luc dang ghi, file goc KHONG bi hong.
    """
    tmp_path = target_path.with_suffix(target_path.suffix + '.tmp')
    if save_func:
        save_func(tmp_path)
    else:
        with open(tmp_path, 'wb') as f:
            pickle.dump(obj, f)
    shutil.move(str(tmp_path), str(target_path))
    print(f"[SAVE] Atomic write thanh cong: {target_path.name}")


def main():
    # 1. Load và Preprocess Data
    loader = DataLoader(RATINGS_PATH, MOVIES_PATH, USERS_PATH)
    ratings = loader.load_ratings()
    
    preprocessor = DataPreprocessor()
    ratings_mapped = preprocessor.map_ids(ratings)
    
    # Chia Train/Test theo Timestamp (tránh data leakage)
    train_df, test_df = preprocessor.time_based_split(ratings_mapped, test_ratio=0.2)
    
    # 2. Khởi tạo Model
    # n_factors: 50-100 là giá trị tối ưu cho tập 1M
    # reg: 0.02 giúp kìm hãm overfitting hiệu quả
    model = FunkSVDModel(n_factors=50, n_epochs=10, lr=0.005, reg=0.02)
    
    # 3. Training
    start_time = time.time()
    model.fit(train_df)
    train_time = time.time() - start_time
    print(f"\nThoi gian training: {train_time:.2f} giay")
    
    # 4. Evaluation
    metrics = Evaluator.evaluate(model, test_df, k=10)
    
    print("\n" + "="*40)
    print("KET QUA DANH GIA MO HINH (FUNKSVD)")
    print("="*40)
    print(f"RMSE    : {metrics['RMSE']}")
    print(f"MAE     : {metrics['MAE']}")
    print(f"NDCG@10 : {metrics['NDCG@K']}")
    print("-" * 40)
    print("Giai thich: NDCG@10 > 0.8 cho thay thu tu goi y rat sat voi gu user.")
    print("="*40)
    
    # 5. Lưu model (Atomic Write — an toan khi server dang chay)
    model_path = MODEL_OUTPUT_DIR / 'funksvd_model.pkl'
    atomic_save(None, model_path, save_func=model.save)

    # 6. Lưu ID mappings (de engine_wrapper load khop voi model)
    mappings_path = MODEL_OUTPUT_DIR / 'id_mappings.pkl'
    mappings = {
        "user2idx": preprocessor.user2idx,
        "idx2user": preprocessor.idx2user,
        "movie2idx": preprocessor.movie2idx,
        "idx2movie": preprocessor.idx2movie,
    }
    atomic_save(mappings, mappings_path)
    print(f"[SAVE] ID mappings: {len(preprocessor.user2idx)} users, {len(preprocessor.movie2idx)} movies")

if __name__ == "__main__":
    main()

