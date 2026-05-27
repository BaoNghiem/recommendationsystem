import numpy as np
import pickle
from pathlib import Path

class FunkSVDModel:
    """
    Triển khai thuật toán FunkSVD (Matrix Factorization).
    Học latent factors của User và Item bằng Stochastic Gradient Descent (SGD).
    """
    def __init__(self, n_factors=50, n_epochs=20, lr=0.005, reg=0.02):
        """
        n_factors: Số lượng đặc trưng ẩn (latent factors).
        n_epochs: Số lần duyệt qua toàn bộ tập dữ liệu.
        lr: Learning rate (tốc độ học).
        reg: Regularization parameter (lambda) để tránh overfitting.
        """
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        
        self.user_factors = None
        self.item_factors = None
        self.global_mean = 0

    def fit(self, train_df):
        """
        Train mô hình bằng SGD.
        train_df: DataFrame chứa [user_idx, movie_idx, rating]
        """
        n_users = train_df['user_idx'].max() + 1
        n_items = train_df['movie_idx'].max() + 1
        
        # Khởi tạo ma trận Latent Factors bằng phân phối chuẩn (Normal Distribution)
        # scale=1./n_factors giúp các giá trị ban đầu nhỏ, ổn định gradient.
        self.user_factors = np.random.normal(scale=1./self.n_factors, size=(n_users, self.n_factors))
        self.item_factors = np.random.normal(scale=1./self.n_factors, size=(n_items, self.n_factors))
        self.global_mean = train_df['rating'].mean()

        print(f"Bat dau Training FunkSVD ({self.n_epochs} epochs, {self.n_factors} factors)...")
        
        # Tối ưu hóa: Chuyển sang mảng numpy để truy cập vùng nhớ liên tục (nhanh hơn pandas)
        u_indices = train_df['user_idx'].values
        m_indices = train_df['movie_idx'].values
        ratings = train_df['rating'].values

        for epoch in range(self.n_epochs):
            total_error = 0
            # Lưu ý: Ở đây dùng vòng lặp SGD trên từng rating (đúng bản chất FunkSVD)
            # Trong thực tế, có thể dùng Numba để tăng tốc vòng lặp này lên 100 lần.
            for i in range(len(ratings)):
                u, m, r = u_indices[i], m_indices[i], ratings[i]
                
                # Dự đoán điểm: r_hat = P_u dot Q_m
                # Đây là tổng hợp các tương tác ẩn giữa User và Movie
                prediction = np.dot(self.user_factors[u], self.item_factors[m])
                error = r - prediction
                total_error += error**2

                # Cập nhật ma trận P và Q theo hướng ngược chiều Gradient
                # reg * factor là thành phần Regularization để kìm hãm model không học quá chi tiết tập train
                u_f = self.user_factors[u]
                m_f = self.item_factors[m]
                
                self.user_factors[u] += self.lr * (error * m_f - self.reg * u_f)
                self.item_factors[m] += self.lr * (error * u_f - self.reg * m_f)
            
            rmse = np.sqrt(total_error / len(ratings))
            print(f"Epoch {epoch+1}/{self.n_epochs} - Train RMSE: {rmse:.4f}")

    def predict(self, user_idx, movie_idx):
        """
        Du doan diem rating cho mot cap (user, item).
        Tra ve dot product cua 2 vector latent factors.
        """
        return float(np.dot(self.user_factors[user_idx], self.item_factors[movie_idx]))

    def predict_batch(self, user_indices, movie_indices):
        """
        Dự đoán hàng loạt (Vectorized) cho tập Test.
        Rất nhanh vì không dùng vòng lặp.
        """
        # Lấy các vector latent factors tương ứng
        P = self.user_factors[user_indices]
        Q = self.item_factors[movie_indices]
        
        # Tính dot product hàng loạt bằng element-wise multiply và sum
        return np.sum(P * Q, axis=1)

    def save(self, path):
        """Lưu model dưới dạng pickle để dùng cho Web App hoặc Inference"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")

    @staticmethod
    def load(path):
        """Tải model đã lưu"""
        with open(path, 'rb') as f:
            return pickle.load(f)
