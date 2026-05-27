import numpy as np
import pandas as pd

class Evaluator:
    """
    Module đánh giá hiệu năng hệ thống gợi ý.
    Tập trung vào Ranking Metrics (NDCG) và Rating Metrics (RMSE).
    """
    
    @staticmethod
    def evaluate(model, test_df, k=10):
        """
        Thực hiện đánh giá đa chỉ số.
        test_df: Chứa user_idx, movie_idx, rating.
        k: Số lượng item trong danh sách Top-K để đánh giá ranking.
        """
        print(f"Dang danh gia model voi Top-K={k}...")
        
        # 1. Dự đoán Vector hóa (Không dùng vòng lặp)
        u_indices = test_df['user_idx'].values
        m_indices = test_df['movie_idx'].values
        actual_ratings = test_df['rating'].values
        
        predictions = model.predict_batch(u_indices, m_indices)

        # 2. Tính RMSE và MAE (Rating Prediction Metrics)
        rmse = np.sqrt(np.mean((actual_ratings - predictions)**2))
        mae = np.mean(np.abs(actual_ratings - predictions))

        # 3. Tính NDCG@K (Ranking Metric)
        # NDCG yêu cầu group theo từng User để xem thứ tự gợi ý đúng hay sai
        results_df = test_df.copy()
        results_df['pred'] = predictions
        
        ndcgs = []
        
        # Groupby user để tính NDCG
        for user_idx, group in results_df.groupby('user_idx'):
            if len(group) < 2: # Bỏ qua user có quá ít dữ liệu test để xếp hạng
                continue
            
            # Sắp xếp rating thực tế để lấy thứ tự lý tưởng (Ideal DCG)
            y_true_sorted = group.sort_values('rating', ascending=False)['rating'].values
            
            # Sắp xếp rating thực tế dựa trên điểm dự đoán của model (Actual DCG)
            y_pred_ranked = group.sort_values('pred', ascending=False)['rating'].values
            
            ndcg_val = Evaluator._calculate_ndcg(y_pred_ranked, y_true_sorted, k)
            ndcgs.append(ndcg_val)

        return {
            'RMSE': round(rmse, 4),
            'MAE': round(mae, 4),
            'NDCG@K': round(np.mean(ndcgs), 4) if ndcgs else 0
        }

    @staticmethod
    def _calculate_ndcg(rel_pred, rel_true, k):
        """Công thức tính NDCG@K cho 1 user"""
        def dcg(rel, k):
            rel = rel[:k]
            # Công thức: rel_i / log2(i + 1)
            # Ở đây dùng (2^rel - 1) để nhấn mạnh các phim có rating cao (4, 5 sao)
            return np.sum((2**rel - 1) / np.log2(np.arange(2, len(rel) + 2)))

        idcg_val = dcg(rel_true, k)
        if idcg_val == 0:
            return 0
        return dcg(rel_pred, k) / idcg_val
