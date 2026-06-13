-- ============================================================
-- MIGRATION PHASE 3: Video Streaming & Watch History
-- Chạy: psql -U postgres -d movie_db -f migration_phase3.sql
-- Mục đích:
--   1. Tạo bảng movie_videos (lưu metadata video từng tập/phim lẻ)
--   2. Tạo bảng watch_history (lưu tiến độ xem của user)
--   3. Tạo index tối ưu cho cả hai bảng
-- ============================================================

-- BƯỚC 1: Tạo bảng movie_videos
-- Unified design: episode_no = NULL → phim lẻ | episode_no = 1,2,3... → phim bộ
CREATE TABLE IF NOT EXISTS movie_videos (
    id              SERIAL PRIMARY KEY,
    movie_id        INT NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    episode_no      INT DEFAULT NULL,           -- NULL = phim lẻ; 1,2,3... = số tập
    season_no       INT DEFAULT 1,              -- mùa (hầu hết = 1)
    episode_title   VARCHAR(300),               -- "Tập 1: Khởi đầu" (tuỳ chọn)
    video_url       VARCHAR(500) NOT NULL,       -- path: /api/uploads/videos/...
    duration_mins   INT,                         -- thời lượng (phút)
    video_quality   VARCHAR(10) DEFAULT '720p', -- '480p' | '720p' | '1080p'
    file_size_mb    FLOAT,                       -- dung lượng file (MB)
    uploaded_at     TIMESTAMP DEFAULT NOW(),

    -- Mỗi tập/phim chỉ có đúng 1 video
    UNIQUE (movie_id, season_no, episode_no)
);

-- BƯỚC 2: Tạo bảng watch_history
-- UNIQUE(user_id, movie_id) → 1 user-1 phim = 1 record, cập nhật liên tục
CREATE TABLE IF NOT EXISTS watch_history (
    id                  SERIAL PRIMARY KEY,
    user_id             INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id            INT NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    episode_no          INT DEFAULT NULL,       -- NULL = phim lẻ; số tập đang xem
    season_no           INT DEFAULT 1,
    watched_at          TIMESTAMP DEFAULT NOW(),
    last_position_secs  INT DEFAULT 0,          -- giây dừng lại (resume)
    watch_percent       FLOAT DEFAULT 0.0,      -- 0.0 → 1.0 (% đã xem)
    is_completed        BOOLEAN DEFAULT FALSE,  -- TRUE khi watch_percent >= 0.85

    -- 1 user chỉ có 1 entry per phim (ON CONFLICT DO UPDATE)
    UNIQUE (user_id, movie_id)
);

-- BƯỚC 3: Index tối ưu
CREATE INDEX IF NOT EXISTS idx_mv_movie_id   ON movie_videos(movie_id);
CREATE INDEX IF NOT EXISTS idx_mv_episode    ON movie_videos(movie_id, season_no, episode_no);

CREATE INDEX IF NOT EXISTS idx_wh_user_id    ON watch_history(user_id);
CREATE INDEX IF NOT EXISTS idx_wh_movie_id   ON watch_history(movie_id);
CREATE INDEX IF NOT EXISTS idx_wh_watched_at ON watch_history(watched_at DESC);
CREATE INDEX IF NOT EXISTS idx_wh_incomplete ON watch_history(user_id) WHERE is_completed = FALSE;

-- BƯỚC 4: Kiểm tra kết quả
SELECT
    (SELECT COUNT(*) FROM movie_videos)   AS total_videos,
    (SELECT COUNT(*) FROM watch_history)  AS total_watch_history;
