"""
Recommendation Engine Wrapper — Phase 3
========================================
Singleton quan ly AI model (FunkSVD + Content-Based + Hybrid).

Phan loai User:
  - User cu (< 7001): FunkSVD (da train trong .pkl)
  - User moi (>= 7001):
      + Co rating >= 4 sao: Content-Based (Cosine Similarity hat giong)
      + Chua rating:        Popularity-Based (avg rating cao, > 50 luot)

Moi log/print deu dung ASCII-safe de tranh loi charmap tren Windows.
"""
import pickle
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Thiet lap path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from config.settings import MODEL_OUTPUT_DIR, RATINGS_PATH, MOVIES_PATH, USERS_PATH
from src.models.funk_svd import FunkSVDModel
from src.models.content_based import ContentBasedModel
from src.models.hybrid_recommender import HybridRecommender
from src.data.data_loader import DataLoader
from src.data.preprocessor import DataPreprocessor

# Ranh gioi giua legacy user va real user
NEW_USER_THRESHOLD = 7001

# Nguong rating de tu dong fold-in user moi vao SVD
FOLD_IN_THRESHOLD = 5

# Nguong rating moi de canh bao retrain
RETRAIN_THRESHOLD = 1000


class RecommendationEngine:
    """
    Singleton Wrapper de quan ly viec load model AI vao RAM.
    Load day du data mapping de Hybrid Engine hoat dong chinh xac.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecommendationEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        print("--- [ENGINE] DANG KHOI TAO AI ENGINE... ---")
        try:
            # 1. Load FunkSVD da train tu Giai doan 2
            model_path = MODEL_OUTPUT_DIR / 'funksvd_model.pkl'
            self.svd_model = FunkSVDModel.load(model_path)

            # 2. Load du lieu goc
            loader = DataLoader(RATINGS_PATH, MOVIES_PATH, USERS_PATH)
            ratings = loader.load_ratings()
            movies = loader.load_movies()
            users = loader.load_users()

            # 2b. NAP THEM phim moi va user moi tu DB (cho Content-Based va users_processed)
            try:
                from src.database.db_config import DatabaseConnector
                conn = DatabaseConnector.get_connection()
                cur = conn.cursor()

                # Nap phim moi tu DB
                # NOTE (Phase 2): Sau migration, bang movies van giu genres_orig (text).
                # AI pipeline (FeatureEngineer.process_movies) doc cot 'genres' la text
                # va tu parse thanh binary multi-hot — KHONG phu thuoc vao bang movie_genres.
                # Bang movie_genres chi phuc vu Filter API (by-genre endpoint).
                cur.execute("""
                    SELECT movie_id, title, genres_orig
                    FROM movies
                    WHERE movie_id > 3883
                """)
                new_movie_rows = cur.fetchall()
                if new_movie_rows:
                    new_movies_df = pd.DataFrame(new_movie_rows, columns=["movie_id", "title", "genres"])
                    movies = pd.concat([movies, new_movies_df], ignore_index=True)
                    movies = movies.drop_duplicates(subset=["movie_id"], keep="last")

                # Nap user moi tu DB
                cur.execute("""
                    SELECT user_id,
                           COALESCE(gender, 'M') AS gender,
                           COALESCE(age, 25) AS age,
                           COALESCE(occupation, 0) AS occupation
                    FROM users WHERE user_id >= %s
                """, (NEW_USER_THRESHOLD,))
                new_user_rows = cur.fetchall()
                if new_user_rows:
                    new_users_df = pd.DataFrame(new_user_rows, columns=["user_id", "gender", "age", "occupation"])
                    users = pd.concat([users, new_users_df], ignore_index=True)
                    users = users.drop_duplicates(subset=["user_id"], keep="last")

                # Nap ratings tu DB de tao train_df
                cur.execute("SELECT user_id, movie_id, rating, timestamp FROM ratings")
                db_rows = cur.fetchall()
                db_ratings = pd.DataFrame(db_rows, columns=["user_id", "movie_id", "rating", "timestamp"])
                ratings = pd.concat([ratings, db_ratings], ignore_index=True)
                ratings = ratings.drop_duplicates(subset=["user_id", "movie_id"], keep="last")
                ratings = ratings.sort_values("timestamp").reset_index(drop=True)

                cur.close()
                conn.close()
                print(f"[ENGINE] Merged DB: {len(ratings)} ratings, {len(movies)} movies, {len(users)} users")
            except Exception as e:
                print(f"[ENGINE] Khong the nap DB (se dung .dat only): {e}")

            # 2c. UU TIEN load mappings da luu tu lan retrain truoc (dam bao khop model)
            mappings_path = MODEL_OUTPUT_DIR / 'id_mappings.pkl'
            if mappings_path.exists():
                with open(mappings_path, 'rb') as f:
                    saved_maps = pickle.load(f)
                preprocessor = DataPreprocessor()
                preprocessor.user2idx = saved_maps["user2idx"]
                preprocessor.idx2user = saved_maps["idx2user"]
                preprocessor.movie2idx = saved_maps["movie2idx"]
                preprocessor.idx2movie = saved_maps["idx2movie"]

                # Map ratings voi mapping da luu
                ratings['user_idx'] = ratings['user_id'].map(preprocessor.user2idx)
                ratings['movie_idx'] = ratings['movie_id'].map(preprocessor.movie2idx)
                ratings = ratings.dropna(subset=['user_idx', 'movie_idx'])
                ratings['user_idx'] = ratings['user_idx'].astype(int)
                ratings['movie_idx'] = ratings['movie_idx'].astype(int)

                self.train_df, _ = preprocessor.time_based_split(ratings)
                print(f"[ENGINE] Loaded saved mappings: "
                      f"{len(preprocessor.user2idx)} users, {len(preprocessor.movie2idx)} movies")
            else:
                # Fallback: tao mapping moi tu data (co the khong khop model)
                preprocessor = DataPreprocessor()
                mapped_ratings = preprocessor.map_ids(ratings)
                self.train_df, _ = preprocessor.time_based_split(mapped_ratings)
                print(f"[ENGINE] No saved mappings, created new from data")

            # Luu mapping dictionaries
            self.user2idx = preprocessor.user2idx     # user_id -> user_idx
            self.idx2movie = preprocessor.idx2movie   # movie_idx -> movie_id
            # BUG FIX: Dung truc tiep preprocessor.movie2idx (movie_id -> movie_idx)
            # KHONG rebuild bang cach dao nguoc idx2movie, vi reload_content_based() se
            # cap nhat idx2movie sau nay khien hai dict bi desync nhau.
            self.movie2idx = preprocessor.movie2idx   # movie_id -> movie_idx

            # Kiem tra tuong thich voi model da train
            n_model_users = self.svd_model.user_factors.shape[0]
            n_model_items = self.svd_model.item_factors.shape[0]
            n_map_users = len(self.user2idx)
            n_map_items = len(self.movie2idx)
            print(f"[ENGINE] Model: {n_model_users} users x {n_model_items} items | "
                  f"Mapping: {n_map_users} users x {n_map_items} items")

            # 3. Tao users_processed voi cot user_idx va gender_mapped
            self.users_processed = users.copy()
            self.users_processed['user_idx'] = self.users_processed['user_id'].map(self.user2idx)
            self.users_processed['gender_mapped'] = (self.users_processed['gender'] == 'M').astype(int)

            # 4. Khoi tao Content-Based
            self.cb_model = ContentBasedModel()
            try:
                from src.features.feature_engineering import FeatureEngineer
                movies_proc = FeatureEngineer.process_movies(movies)
                movies_proc['movie_idx'] = movies_proc['movie_id'].map(preprocessor.movie2idx)
                movies_proc = movies_proc.dropna(subset=['movie_idx'])
                movies_proc['movie_idx'] = movies_proc['movie_idx'].astype(int)
                self.cb_model.fit(movies_proc)
            except Exception as e:
                print(f"[ENGINE] Content-Based khong load duoc (se dung fallback): {e}")

            # 5. Ket hop thanh Hybrid Engine
            self.hybrid_engine = HybridRecommender(self.svd_model, self.cb_model)

            # 6. Fit metadata (lich su user, popularity, demographics)
            self.hybrid_engine.fit_hybrid_metadata(self.train_df, self.users_processed)

            # 7. Cache avg rating per movie (tu DB) de predict chinh xac cho cold-start
            self.avg_rating_cache = {}  # movie_id -> avg_rating
            self._build_avg_rating_cache()

            # 8. Luu tru fold-in user vectors: user_id -> np.array(n_factors)
            self.folded_in_users = {}

            # 9. Kiem tra dieu kien retrain
            self._check_retrain_condition()

            self._initialized = True
            print("--- [ENGINE] AI ENGINE DA SAN SANG! ---")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"--- [ENGINE] LOI KHI LOAD MODEL: {e} ---")
            self.hybrid_engine = None
            self.user2idx = {}
            self.idx2movie = {}
            self.movie2idx = {}
            self.cb_model = None
            self.avg_rating_cache = {}
            self.folded_in_users = {}

    # ══════════════════════════════════════════════════════════════
    # CACHE: Avg rating per movie (cho cold-start predict)
    # ══════════════════════════════════════════════════════════════
    def _build_avg_rating_cache(self):
        """Cache diem trung binh cua cong dong cho tung phim (Dictionary, O(1) lookup)."""
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT movie_id, ROUND(AVG(rating)::numeric, 2) AS avg_r
                FROM ratings
                GROUP BY movie_id
            """)
            for row in cur.fetchall():
                self.avg_rating_cache[row[0]] = float(row[1])
            cur.close()
            conn.close()
            print(f"[ENGINE] Cached avg rating cho {len(self.avg_rating_cache)} phim")
        except Exception as e:
            print(f"[ENGINE] Khong the build avg_rating_cache: {e}")

    # ══════════════════════════════════════════════════════════════
    # RETRAIN CHECK: Canh bao khi co qua nhieu rating moi
    # ══════════════════════════════════════════════════════════════
    def _check_retrain_condition(self):
        """So sanh so rating trong DB vs so rating da train. Canh bao neu vuot nguong."""
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM ratings")
            db_count = cur.fetchone()[0]
            cur.close()
            conn.close()

            trained_count = len(self.train_df)
            new_ratings = db_count - trained_count

            if new_ratings >= RETRAIN_THRESHOLD:
                print(f"\n{'='*60}")
                print(f"  [RETRAIN WARNING] {new_ratings} ratings moi ke tu lan train cuoi!")
                print(f"  DB: {db_count} | Trained: {trained_count}")
                print(f"  => Nen chay Full Retrain de cap nhat latent factors.")
                print(f"{'='*60}\n")
            else:
                print(f"[ENGINE] Retrain check: {new_ratings} new ratings (nguong: {RETRAIN_THRESHOLD})")

            self._trained_rating_count = trained_count
            self._db_rating_count = db_count
        except Exception as e:
            print(f"[ENGINE] Retrain check failed: {e}")

    # ════════════════════════════════════════════════════════════
    # HOT RELOAD: Cap nhat Content-Based khi co phim moi tu Admin
    # ════════════════════════════════════════════════════════════
    def reload_content_based(self):
        """
        Hot-reload Content-Based similarity matrix.
        Goi sau khi Admin them/sua phim de model phan hoi ngay ma khong phai restart server.
        Chay trong background thread (khong block API).

        FIX Cold-Start: Phan cong movie_idx tam thoi cho phim moi (chua co trong mapping
        cua model da train), dam bao chung duoc dua vao CB similarity matrix ngay lap tuc.
        """
        print("[ENGINE] Bat dau hot-reload Content-Based model...")
        try:
            from src.database.db_config import DatabaseConnector
            from src.data.data_loader import DataLoader
            from src.features.feature_engineering import FeatureEngineer
            from config.settings import MOVIES_PATH, RATINGS_PATH, USERS_PATH

            # 1. Lay tat ca phim moi tu DB (movie_id > 3883)
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT movie_id, title, genres_orig
                FROM movies
                WHERE movie_id > 3883
            """)
            new_movie_rows = cur.fetchall()
            cur.close()
            conn.close()

            # 2. Merge voi dat file goc
            loader = DataLoader(MOVIES_PATH, RATINGS_PATH, USERS_PATH)
            movies = loader.load_movies()
            if new_movie_rows:
                new_df = pd.DataFrame(new_movie_rows,
                                      columns=["movie_id", "title", "genres"])
                movies = pd.concat([movies, new_df], ignore_index=True)
                movies = movies.drop_duplicates(subset=["movie_id"], keep="last")

            # 3. Re-fit Content-Based
            movies_proc = FeatureEngineer.process_movies(movies)
            movies_proc["movie_idx"] = movies_proc["movie_id"].map(self.movie2idx)

            # --- COLD-START FIX: Phan cong idx tam thoi cho phim chua co trong mapping ---
            # Tim idx tiep theo sau max idx hien tai trong model
            next_new_idx = (
                int(movies_proc["movie_idx"].dropna().max()) + 1
                if movies_proc["movie_idx"].notna().any()
                else len(self.movie2idx)
            )
            # Cap nhat mapping tam thoi (chi dung cho CB, khong anh huong SVD)
            self._new_movie_temp_map = {}  # movie_id -> temp_idx
            for _, row in movies_proc[movies_proc["movie_idx"].isna()].iterrows():
                mid = int(row["movie_id"])
                movies_proc.loc[movies_proc["movie_id"] == mid, "movie_idx"] = next_new_idx
                self._new_movie_temp_map[mid] = next_new_idx
                # BUG #5 FIX: Sync ca hai dict de tranh desync
                self.idx2movie[next_new_idx] = mid
                self.movie2idx[mid] = next_new_idx  # <-- quan trong: cap nhat nguoc lai
                next_new_idx += 1
            # --------------------------------------------------------------------------

            movies_proc = movies_proc.dropna(subset=["movie_idx"])
            movies_proc["movie_idx"] = movies_proc["movie_idx"].astype(int)

            new_cb = ContentBasedModel()
            new_cb.fit(movies_proc)

            # 4. Atomic replace (tranh race condition)
            self.cb_model = new_cb
            self.hybrid_engine = HybridRecommender(self.svd_model, self.cb_model)
            self.hybrid_engine.fit_hybrid_metadata(self.train_df, self.users_processed)

            n_new = len(getattr(self, '_new_movie_temp_map', {}))
            print(f"[ENGINE] Hot-reload xong: {len(movies)} phim trong CB matrix "
                  f"({n_new} phim moi duoc them voi idx tam thoi)")
        except Exception as e:
            print(f"[ENGINE] Hot-reload that bai (engine khong anh huong): {e}")

    # ══════════════════════════════════════════════════════════════
    # FOLD-IN: Tinh user vector moi tu item_factors (Online Learning)
    # ══════════════════════════════════════════════════════════════
    def fold_in_user(self, user_id):
        """
        Ky thuat Fold-in cho SVD:
        Giu co dinh item_factors (Q), giai bai toan Least Squares de tim p_u:
            p_u = argmin ||R_u - p_u * Q_rated||^2 + lambda * ||p_u||^2

        Tuong duong giai: p_u = (Q_rated^T * Q_rated + lambda*I)^(-1) * Q_rated^T * r_u

        Dieu kien: User phai co >= FOLD_IN_THRESHOLD ratings.
        """
        if not self.svd_model or self.svd_model.item_factors is None:
            return None

        # Lay tat ca ratings cua user tu DB
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT movie_id, rating FROM ratings WHERE user_id = %s",
                (user_id,)
            )
            user_ratings = cur.fetchall()  # [(movie_id, rating), ...]
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[FOLD-IN] DB error for user {user_id}: {e}")
            return None

        if len(user_ratings) < FOLD_IN_THRESHOLD:
            return None

        # Loc chi nhung phim co trong model
        Q = self.svd_model.item_factors  # shape: (n_items, n_factors)
        valid_ratings = []
        for movie_id, rating in user_ratings:
            movie_idx = self.movie2idx.get(movie_id)
            if movie_idx is not None and movie_idx < Q.shape[0]:
                valid_ratings.append((movie_idx, float(rating)))

        if len(valid_ratings) < FOLD_IN_THRESHOLD:
            return None

        # Xay dung ma tran Q_rated va vector r_u
        rated_indices = [v[0] for v in valid_ratings]
        ratings_vec = np.array([v[1] for v in valid_ratings])  # (k,)
        Q_rated = Q[rated_indices]  # (k, n_factors)

        # Giai Least Squares co Regularization:
        # p_u = (Q_rated^T * Q_rated + reg*I)^(-1) * Q_rated^T * r_u
        reg = self.svd_model.reg if hasattr(self.svd_model, 'reg') else 0.02
        n_factors = Q.shape[1]
        A = Q_rated.T @ Q_rated + reg * np.eye(n_factors)  # (f, f)
        b = Q_rated.T @ ratings_vec                         # (f,)

        try:
            p_u = np.linalg.solve(A, b)  # (n_factors,)
        except np.linalg.LinAlgError:
            print(f"[FOLD-IN] Singular matrix for user {user_id}, using lstsq")
            p_u, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

        # Cache ket qua
        self.folded_in_users[user_id] = p_u
        print(
            f"[FOLD-IN] User {user_id}: folded in with {len(valid_ratings)} ratings "
            f"-> vector norm: {np.linalg.norm(p_u):.4f}"
        )
        return p_u

    # ══════════════════════════════════════════════════════════════
    # INVALIDATE: Xoa cache fold-in khi user co rating moi
    # ══════════════════════════════════════════════════════════════
    def invalidate_fold_in_cache(self, user_id):
        """
        Xoa cache fold-in cua 1 user khi ho vua rate phim moi.
        Lan goi get_recommendations() tiep theo se tu dong tinh lai vector.
        """
        if user_id in self.folded_in_users:
            del self.folded_in_users[user_id]
            print(f"[FOLD-IN] Cache invalidated for user {user_id}")

    # ══════════════════════════════════════════════════════════════
    # HELPER: Lay danh sach phim da rated tu DB
    # ══════════════════════════════════════════════════════════════
    def get_rated_movies(self, user_id):
        """Lay danh sach ID cac phim ma User da tung danh gia (tu DB)."""
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT movie_id FROM ratings WHERE user_id = %s", (user_id,))
            rated = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
            return rated
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════
    # HELPER: Lay phim da rated CAO (>= min_rating) tu DB
    # ══════════════════════════════════════════════════════════════
    def get_high_rated_movies(self, user_id, min_rating=4.0):
        """Lay phim ma user da danh gia >= min_rating sao (hat giong cho CB)."""
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT movie_id, rating FROM ratings "
                "WHERE user_id = %s AND rating >= %s "
                "ORDER BY rating DESC, timestamp DESC",
                (user_id, min_rating),
            )
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows  # [(movie_id, rating), ...]
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════
    # PREDICT: Du doan diem rating cho 1 cap (user, movie)
    # ══════════════════════════════════════════════════════════════
    def predict_rating(self, user_id, movie_id):
        """
        Du doan diem rating cho 1 cap (user, movie).
        Uu tien: SVD trained -> Fold-in -> Avg rating cong dong.
        """
        try:
            movie_idx = self.movie2idx.get(movie_id)

            # 1) User co trong model SVD (legacy, da train)
            user_idx = self.user2idx.get(user_id)
            if user_idx is not None and movie_idx is not None:
                pred = self.svd_model.predict(user_idx, movie_idx)
                return round(float(np.clip(pred, 0.5, 5.0)), 1)

            # 2) User da duoc fold-in
            if user_id in self.folded_in_users and movie_idx is not None:
                p_u = self.folded_in_users[user_id]
                q_m = self.svd_model.item_factors[movie_idx]
                pred = float(np.dot(p_u, q_m))
                return round(float(np.clip(pred, 0.5, 5.0)), 1)

            # 3) Tra ve avg rating cong dong cho phim do (thay vi 3.5 cung)
            avg = self.avg_rating_cache.get(movie_id)
            if avg is not None:
                return round(avg, 1)

            # 4) Fallback: global mean
            return round(float(self.svd_model.global_mean), 1)
        except Exception as e:
            print(f"[ENGINE] Loi predict: {e}")
            return 3.0

    # ══════════════════════════════════════════════════════════════
    # POPULARITY: Phim pho bien nhat (fallback + cold-start)
    # ══════════════════════════════════════════════════════════════
    def get_popular_movies(self, top_n=20):
        """
        Lay danh sach phim pho bien nhat.
        Uu tien: model popularity -> DB (avg rating cao, count > 50).
        """
        # Thu tu model metadata truoc
        try:
            if self.hybrid_engine and self.hybrid_engine.global_popularity is not None:
                top_idx = self.hybrid_engine.global_popularity.index[:top_n].tolist()
                result = [int(self.idx2movie.get(idx, idx)) for idx in top_idx if idx in self.idx2movie]
                if result:
                    return result
        except Exception as e:
            print(f"[ENGINE] Loi get_popular_movies (model): {e}")

        # Fallback: Query truc tiep DB (avg rating cao, > 50 luot)
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT r.movie_id
                FROM ratings r
                GROUP BY r.movie_id
                HAVING COUNT(*) > 50
                ORDER BY AVG(r.rating) DESC, COUNT(*) DESC
                LIMIT %s
            """, (top_n,))
            ids = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
            return ids
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════
    # CONTENT-BASED: Goi y dua tren hat giong (cho user moi)
    # ══════════════════════════════════════════════════════════════
    def get_content_based_recommendations(self, seed_movie_ids, top_n=20, exclude_ids=None):
        """
        Content-Based Filtering cho user moi:
        - Lay cac phim 'hat giong' (seed) ma user da danh gia cao.
        - Dung ma tran Cosine Similarity de tim phim tuong dong nhat.
        - Tra ve danh sach movie_id sap xep theo do tuong dong giam dan.

        COLD-START FIX: Neu seed la phim moi (chua co trong CB matrix),
        doi sang tim phim co cung the loai tu DB.

        Args:
            seed_movie_ids: list of movie_id (phim user thich, >= 4 sao)
            top_n: so phim goi y
            exclude_ids: set of movie_id da xem (de loai bo)

        Returns:
            list[int]: movie_ids duoc goi y
        """
        if not self.cb_model or self.cb_model.movie_sim_matrix is None:
            print("[ENGINE-CB] Content-Based model chua san sang, fallback popularity")
            return self.get_popular_movies(top_n)

        exclude_ids = set(exclude_ids or [])

        # Map movie_id -> movie_idx (noi bo model)
        # Uu tien: movie2idx (tu model) -> _new_movie_temp_map (phim moi hot-reload)
        temp_map = getattr(self, '_new_movie_temp_map', {})
        seed_indices = []
        unmapped_seeds = []  # phim moi chua co trong bat ky map nao
        for mid in seed_movie_ids:
            idx = self.movie2idx.get(mid) or temp_map.get(mid)
            if idx is not None and idx in self.cb_model.movie_idx_to_pos:
                seed_indices.append(idx)
            else:
                unmapped_seeds.append(mid)

        # COLD-START: Neu co phim moi chua hot-reload, lay genre fallback tu DB
        if unmapped_seeds and not seed_indices:
            print(f"[ENGINE-CB] {len(unmapped_seeds)} seed(s) la phim moi chua trong CB, "
                  f"dung genre-based fallback")
            return self._genre_based_fallback(unmapped_seeds, top_n, exclude_ids)

        if not seed_indices:
            print(f"[ENGINE-CB] Khong map duoc seed movies, fallback popularity")
            return self.get_popular_movies(top_n)

        # Tinh diem tuong dong trung binh cho moi phim ung vien
        scores = {}
        for movie_idx, pos in self.cb_model.movie_idx_to_pos.items():
            # Bo qua chinh cac seed
            movie_id = self.idx2movie.get(movie_idx)
            if movie_id is None or movie_id in exclude_ids:
                continue
            if movie_idx in seed_indices:
                continue

            # Diem = trung binh cosine similarity voi tat ca seed
            seed_positions = [self.cb_model.movie_idx_to_pos[si] for si in seed_indices]
            sim_values = self.cb_model.movie_sim_matrix[pos][seed_positions]
            avg_sim = float(np.mean(sim_values))
            scores[movie_id] = avg_sim

        # Sap xep giam dan theo similarity
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        result = [int(mid) for mid, score in ranked[:top_n]]

        print(f"[ENGINE-CB] Content-Based: {len(seed_indices)} seeds -> {len(result)} recommendations")
        return result

    # ══════════════════════════════════════════════════════════════
    # COLD-START GENRE FALLBACK: Cho phim moi chua vao CB matrix
    # ══════════════════════════════════════════════════════════════
    def _genre_based_fallback(self, seed_movie_ids, top_n=20, exclude_ids=None):
        """
        Fallback cho cold-start: tim phim cung the loai voi seed movies.
        Su dung khi seed movies la phim moi (>3883) chua duoc hot-reload vao CB matrix.
        Uu tien phim co avg_rating cao va nhieu luot danh gia.
        """
        exclude_ids = set(exclude_ids or [])
        try:
            from src.database.db_config import DatabaseConnector
            conn = DatabaseConnector.get_connection()
            cur = conn.cursor()

            # Lay genres cua cac seed movies
            cur.execute(
                "SELECT genres_orig FROM movies WHERE movie_id = ANY(%s)",
                (list(seed_movie_ids),)
            )
            genre_rows = cur.fetchall()
            if not genre_rows:
                cur.close(); conn.close()
                return self.get_popular_movies(top_n)

            # Tong hop tat ca genres
            genres_set = set()
            for row in genre_rows:
                if row[0]:
                    for g in row[0].split('|'):
                        genres_set.add(g.strip())

            if not genres_set:
                cur.close(); conn.close()
                return self.get_popular_movies(top_n)

            # Tim phim co it nhat 1 genre trung khop, sap xep theo avg_rating
            genre_conditions = " OR ".join(
                [f"m.genres_orig ILIKE %s" for _ in genres_set]
            )
            params = [f"%{g}%" for g in genres_set] + [top_n * 3]
            cur.execute(f"""
                SELECT m.movie_id,
                       COALESCE(AVG(r.rating), 0) AS avg_r,
                       COUNT(r.rating) AS cnt
                FROM movies m
                LEFT JOIN ratings r ON m.movie_id = r.movie_id
                WHERE ({genre_conditions})
                  AND m.movie_id <= 3883
                GROUP BY m.movie_id
                HAVING COUNT(r.rating) > 20
                ORDER BY avg_r DESC, cnt DESC
                LIMIT %s
            """, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            result = [
                int(row[0]) for row in rows
                if row[0] not in exclude_ids
            ][:top_n]

            print(f"[ENGINE-CB] Genre fallback: genres={genres_set} -> {len(result)} phim")
            return result if result else self.get_popular_movies(top_n)
        except Exception as e:
            print(f"[ENGINE-CB] Genre fallback loi: {e}")
            return self.get_popular_movies(top_n)

    # ══════════════════════════════════════════════════════════════
    # MAIN ENTRY: get_recommendations — CORE LOGIC Phase 3
    # ══════════════════════════════════════════════════════════════
    def get_recommendations(self, user_id, top_n=10):
        """
        Goi logic goi y — LUON tra ve phim, khong bao gio tra ve rong.

        Phan loai:
          1) Engine chua load -> popularity fallback
          2) User co trong model (Legacy hoac da retrain) -> Hybrid (FunkSVD + CB)
          3) User moi (chua train):
             a) Co >= 5 ratings   -> Fold-in SVD (tinh vector ẩn on-the-fly)
             b) Co rating >= 4 sao -> Content-Based (hat giong)
             c) Chua rating        -> Popularity-Based (cold start)
        """
        # === TRUONG HOP 1: Engine chua load ===
        if not self.hybrid_engine:
            print(f">>> [FALLBACK] Engine chua san sang, dung phim pho bien")
            return self.get_popular_movies(top_n), "popularity"

        # === TRUONG HOP 2: User co trong mapping VA model (Legacy hoac da retrain) ===
        user_idx = self.user2idx.get(user_id)

        # Kiem tra user_idx co hop le trong ma tran model khong
        user_in_model = (
            user_idx is not None
            and user_idx < self.svd_model.user_factors.shape[0]
        )

        if user_in_model:
            # User co trong Model -> Goi Hybrid (FunkSVD + Content-Based)
            try:
                movie_indices = self.hybrid_engine.recommend(
                    user_idx, self.users_processed, top_n=top_n
                )
                movie_ids = [
                    int(self.idx2movie.get(idx, idx))
                    for idx in movie_indices
                    if idx in self.idx2movie
                ]
                if movie_ids:
                    return movie_ids, "hybrid"

                print(f">>> [FALLBACK] User {user_id}: hybrid tra ve rong")
                return self.get_popular_movies(top_n), "popularity"
            except Exception as e:
                print(f">>> [FALLBACK] Loi hybrid cho user {user_id}: {e}")
                return self.get_popular_movies(top_n), "popularity"

        # === TRUONG HOP 3: New User (>= 7001 hoac khong trong model) ===
        rated_ids = set(self.get_rated_movies(user_id))
        n_ratings = len(rated_ids)

        # 3a) Co >= FOLD_IN_THRESHOLD ratings -> Thu fold-in vao SVD
        if n_ratings >= FOLD_IN_THRESHOLD:
            # Auto fold-in neu chua co hoac ratings da thay doi
            if user_id not in self.folded_in_users:
                p_u = self.fold_in_user(user_id)
                if p_u is not None:
                    # User da duoc fold-in -> Dung SVD predict de rank
                    print(
                        f">>> [FOLD-IN RECOMMEND] User {user_id}: "
                        f"upgraded to SVD with {n_ratings} ratings"
                    )
                    return self._recommend_folded_in(user_id, top_n, rated_ids), "hybrid_foldin"

            # Neu da co fold-in tu truoc
            if user_id in self.folded_in_users:
                return self._recommend_folded_in(user_id, top_n, rated_ids), "hybrid_foldin"

        # 3b) Co it nhat 1 phim rated >= 4 sao -> Content-Based
        high_rated = self.get_high_rated_movies(user_id, min_rating=4.0)
        if high_rated:
            seed_ids = [r[0] for r in high_rated]
            print(
                f">>> [CONTENT-BASED] New user {user_id}: "
                f"{len(high_rated)} seed(s) rated >= 4 stars"
            )
            cb_results = self.get_content_based_recommendations(
                seed_ids, top_n=top_n, exclude_ids=rated_ids
            )
            if cb_results:
                return cb_results, "content_based"

        # 3c) Chua rating hoac khong du seed -> Cold Start (Popularity)
        print(f">>> [COLD-START] New user {user_id}: dung popularity")
        return self.get_popular_movies(top_n), "popularity"

    # ══════════════════════════════════════════════════════════════
    # RECOMMEND cho user da fold-in: Dung SVD predict de rank
    # ══════════════════════════════════════════════════════════════
    def _recommend_folded_in(self, user_id, top_n, exclude_ids):
        """
        Goi y cho user da fold-in bang cach predict score cho tat ca phim
        chua xem, roi lay top_n cao nhat.
        """
        p_u = self.folded_in_users[user_id]
        Q = self.svd_model.item_factors  # (n_items, n_factors)

        # Predict score cho tat ca item cung luc (vectorized)
        all_scores = Q @ p_u  # (n_items,)

        # Sap xep giam dan
        ranked_indices = np.argsort(all_scores)[::-1]

        results = []
        for movie_idx in ranked_indices:
            movie_id = self.idx2movie.get(int(movie_idx))
            if movie_id is None or movie_id in exclude_ids:
                continue
            results.append(int(movie_id))
            if len(results) >= top_n:
                break

        return results
