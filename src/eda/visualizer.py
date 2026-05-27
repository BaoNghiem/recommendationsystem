import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Force UTF-8 on Windows to prevent charmap errors with Vietnamese text
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass

class Visualizer:
    """
    Module xuất báo cáo biểu đồ (Exploratory Data Analysis).
    Tự động lưu ảnh với độ phân giải cao (300 dpi) để chèn vào báo cáo Word/PDF.
    """
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Thiết lập theme đẹp mắt, phù hợp báo cáo học thuật
        sns.set_theme(style="whitegrid", palette="muted")

    def plot_rating_distribution(self, ratings: pd.DataFrame):
        """1. Biểu đồ phân phối Rating (Bar chart)"""
        print("System log: Action in progress")
        plt.figure(figsize=(10, 6))
        ax = sns.countplot(data=ratings, x='rating', palette='viridis')
        plt.title('Phân phối số sao đánh giá (Rating Distribution)', fontsize=16, fontweight='bold')
        plt.xlabel('Rating (Sao)', fontsize=12)
        plt.ylabel('Số lượng đánh giá', fontsize=12)
        
        # Ghi số liệu trên đỉnh cột
        for p in ax.patches:
            ax.annotate(format(p.get_height(), '.0f'), 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha = 'center', va = 'center', 
                        xytext = (0, 9), 
                        textcoords = 'offset points')
                        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rating_distribution.png', dpi=300)
        plt.close()

    def plot_long_tail(self, ratings: pd.DataFrame):
        """2. Biểu đồ Long-tail Effect (Sự bất đối xứng rating của các phim)"""
        print("System log: Action in progress")
        movie_counts = ratings['movie_id'].value_counts().values
        
        plt.figure(figsize=(12, 6))
        plt.plot(movie_counts, color='crimson', linewidth=2)
        plt.fill_between(range(len(movie_counts)), movie_counts, color='crimson', alpha=0.3)
        plt.title('Hiện tượng "Đuôi dài" (Long-Tail Effect) trong Đánh giá Phim', fontsize=16, fontweight='bold')
        plt.xlabel('Phim (Đã sắp xếp theo độ phổ biến giảm dần)', fontsize=12)
        plt.ylabel('Số lượng đánh giá (Log Scale)', fontsize=12)
        plt.yscale('log') # Trục Y log để thấy rõ cái đuôi kéo dài
        plt.tight_layout()
        plt.savefig(self.output_dir / 'long_tail_effect.png', dpi=300)
        plt.close()

    def plot_activity(self, ratings: pd.DataFrame):
        """3. Biểu đồ mức độ hoạt động của User và số lượt đánh giá của Movie"""
        print("System log: Action in progress")
        user_counts = ratings.groupby('user_id').size()
        movie_counts = ratings.groupby('movie_id').size()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        sns.histplot(user_counts, bins=50, kde=True, ax=ax1, color='royalblue')
        ax1.set_title('Tần suất đánh giá của người dùng', fontsize=14)
        ax1.set_xlabel('Số lượng đánh giá')
        ax1.set_ylabel('Số lượng người dùng')
        ax1.set_xlim(0, 1000)

        sns.histplot(movie_counts, bins=50, kde=True, ax=ax2, color='darkorange')
        ax2.set_title('Mức độ phổ biến của Phim', fontsize=14)
        ax2.set_xlabel('Số lượng đánh giá')
        ax2.set_ylabel('Số lượng Phim')
        ax2.set_xlim(0, 1000)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'activity_distribution.png', dpi=300)
        plt.close()

    def plot_genre_analysis(self, movies_processed: pd.DataFrame):
        """4. Biểu đồ sự phổ biến của các thể loại phim"""
        print("System log: Action in progress")
        # Loại trừ các cột không phải là thể loại
        non_genre_cols = ['movie_id', 'title', 'genres']
        genre_cols = [c for c in movies_processed.columns if c not in non_genre_cols]
        
        # Đếm tổng số phim cho mỗi thể loại
        genre_counts = movies_processed[genre_cols].sum().sort_values(ascending=False)
        
        plt.figure(figsize=(14, 8))
        sns.barplot(x=genre_counts.values, y=genre_counts.index, palette='Spectral')
        plt.title('Số lượng Phim theo từng Thể loại', fontsize=16, fontweight='bold')
        plt.xlabel('Số lượng', fontsize=12)
        plt.ylabel('Thể loại', fontsize=12)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'genre_popularity.png', dpi=300)
        plt.close()

    @staticmethod
    def print_sparsity(ratings: pd.DataFrame):
        """5. In ra màn hình thông số độ thưa (Sparsity) của ma trận"""
        num_users = ratings['user_id'].nunique()
        num_movies = ratings['movie_id'].nunique()
        num_ratings = len(ratings)
        
        total_possible = num_users * num_movies
        sparsity = (1.0 - (num_ratings / total_possible)) * 100
        
        print("\n" + "="*40)
        print("BAO CAO THONG KE DATASET (1M)")
        print("="*40)
        print(f"- Tong so User duy nhat : {num_users:,}")
        print(f"- Tong so Phim duy nhat : {num_movies:,}")
        print(f"- Tong so Danh gia      : {num_ratings:,}")
        print(f"- Kich thuoc Ma tran    : {num_users:,} x {num_movies:,} = {total_possible:,} o")
        print(f"- Do thua (Sparsity)    : {sparsity:.4f}%")
        print("=> Ket luan: Co den {:.4f}% o trong ma tran trong. Day la ly do".format(sparsity))
        print("System log: Action in progress")
        print("="*40 + "\n")
