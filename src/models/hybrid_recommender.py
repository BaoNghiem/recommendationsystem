import numpy as np
import pandas as pd

class HybridRecommender:
    """
    He thong goi y Hybrid: Ket hop FunkSVD va Content-Based.
    Giai quyet Cold Start bang Popularity va Demographics.
    """
    def __init__(self, svd_model, cb_model, alpha=0.8):
        self.svd = svd_model
        self.cb = cb_model
        self.alpha = alpha
        
        self.global_popularity = None
        self.demographic_pop = {} # Luu tru top phim theo Gender/Age
        self.user_history = {} # Luu lai lich su xem cua tung user

    def fit_hybrid_metadata(self, train_df, users_processed):
        """
        Hoc cac thong tin phu de phuc vu Cold Start va Hybrid blending.
        """
        print("Dang phan tich du lieu phu cho Hybrid Engine...")
        
        # 1. Lưu lịch sử xem của User (để Content-based lookup)
        self.user_history = train_df.groupby('user_idx')['movie_idx'].apply(list).to_dict()
        
        # 2. Tính Popularity toàn cục (weighted score)
        movie_stats = train_df.groupby('movie_idx')['rating'].agg(['mean', 'count'])
        # Cong thuc: Score = mean * log(count) -> Can bang giua diem cao va so luong nguoi xem
        movie_stats['pop_score'] = movie_stats['mean'] * np.log1p(movie_stats['count'])
        self.global_popularity = movie_stats.sort_values('pop_score', ascending=False)
        
        # 3. Demographic Popularity (Cold Start theo giới tính)
        # Gộp ratings với info user
        user_ratings = train_df.merge(users_processed[['user_idx', 'gender_mapped']], on='user_idx')
        for gender in [0, 1]: # 0: F, 1: M
            g_ratings = user_ratings[user_ratings['gender_mapped'] == gender]
            g_stats = g_ratings.groupby('movie_idx')['rating'].agg(['mean', 'count'])
            g_stats['score'] = g_stats['mean'] * np.log1p(g_stats['count'])
            self.demographic_pop[gender] = g_stats.sort_values('score', ascending=False).index.tolist()[:50]

    def predict_hybrid(self, user_idx, movie_idx):
        """
        Du doan diem Hybrid: alpha * SVD + (1-alpha) * Content
        """
        # Lay diem tu SVD
        svd_score = self.svd.predict(user_idx, movie_idx)
        
        # Lay diem tu Content-Based
        user_movies = self.user_history.get(user_idx, [])
        cb_score = self.cb.get_content_score(movie_idx, user_movies)
        
        # Chuan hoa cb_score (tu 0-1 sang thang diem 1-5)
        cb_score_scaled = 1 + cb_score * 4
        
        return self.alpha * svd_score + (1 - self.alpha) * cb_score_scaled

    def recommend(self, user_idx, users_df, top_n=10):
        """
        Ham goi y tong quat: Tu dong xu ly Cold Start.
        """
        # TRUONG HOP 1: COLD START (User moi hoac chua co lich su)
        if user_idx not in self.user_history:
            # Thu lay gender de goi y demographic
            user_info = users_df[users_df['user_idx'] == user_idx]
            if not user_info.empty:
                gender = user_info['gender_mapped'].values[0]
                return self.demographic_pop.get(gender, self.global_popularity.index[:top_n].tolist())
            return self.global_popularity.index[:top_n].tolist()
            
        # TRUONG HOP 2: HYBRID FOR EXISTING USERS
        # (Trong thuc te ta se predict cho cac phim chua xem va lay Top N)
        # De demo hieu qua, ta gia dinh lay top tu global pop va re-rank bang Hybrid score
        candidate_movies = self.global_popularity.index[:300] # Lay 300 phim lam ung vien (tang tu 100)
        user_seen = set(self.user_history.get(user_idx, []))
        
        scores = []
        for m_idx in candidate_movies:
            if m_idx in user_seen: continue
            score = self.predict_hybrid(user_idx, m_idx)
            scores.append((m_idx, score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scores[:top_n]]
