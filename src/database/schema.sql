-- ================================================================
-- Database Schema v3 — Movie Recommender System
-- Cập nhật: phản ánh cấu trúc DB thực tế (có đầy đủ các bảng)
-- BUG FIX Issue 8: Schema cũ chỉ có 3 bảng, thiếu toàn bộ metadata
-- ================================================================

-- 1. Xóa tất cả các bảng (thứ tự đúng để tránh lỗi FK)
DROP TABLE IF EXISTS watch_history CASCADE;
DROP TABLE IF EXISTS movie_videos CASCADE;
DROP TABLE IF EXISTS movie_actors CASCADE;
DROP TABLE IF EXISTS movie_directors CASCADE;
DROP TABLE IF EXISTS movie_genres CASCADE;
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS actors CASCADE;
DROP TABLE IF EXISTS directors CASCADE;
DROP TABLE IF EXISTS movies CASCADE;
DROP TABLE IF EXISTS users CASCADE;


-- 2. Bảng Users (thông tin đầy đủ cả legacy + real accounts)
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE,
    password_hash   TEXT,
    gender          CHAR(1),
    age             INT,
    occupation      INT,
    role            VARCHAR(20)  DEFAULT 'user',        -- 'user' | 'admin'
    account_type    VARCHAR(20)  DEFAULT 'real',        -- 'legacy' | 'real'
    is_active       BOOLEAN      DEFAULT TRUE,
    email_verified  BOOLEAN      DEFAULT FALSE,
    verification_token   TEXT,
    token_expires_at     TIMESTAMPTZ,
    reset_token          TEXT,
    reset_token_expires  TIMESTAMPTZ,
    password_changed_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);


-- 3. Bảng Movies (metadata đầy đủ)
CREATE TABLE movies (
    movie_id        INT PRIMARY KEY,
    title           VARCHAR(500),
    genres_orig     TEXT,                               -- "Action|Comedy|Drama"
    release_year    INT,
    country         VARCHAR(100),
    total_episodes  INT,                                -- NULL = phim lẻ, INT = phim bộ
    description     TEXT,
    poster_url      TEXT
);


-- 4. Bảng movie_genres (18 cột binary cho AI + API filter)
CREATE TABLE movie_genres (
    movie_id    INT PRIMARY KEY REFERENCES movies(movie_id) ON DELETE CASCADE,
    action      SMALLINT DEFAULT 0,
    adventure   SMALLINT DEFAULT 0,
    animation   SMALLINT DEFAULT 0,
    childrens   SMALLINT DEFAULT 0,
    comedy      SMALLINT DEFAULT 0,
    crime       SMALLINT DEFAULT 0,
    documentary SMALLINT DEFAULT 0,
    drama       SMALLINT DEFAULT 0,
    fantasy     SMALLINT DEFAULT 0,
    film_noir   SMALLINT DEFAULT 0,
    horror      SMALLINT DEFAULT 0,
    musical     SMALLINT DEFAULT 0,
    mystery     SMALLINT DEFAULT 0,
    romance     SMALLINT DEFAULT 0,
    sci_fi      SMALLINT DEFAULT 0,
    thriller    SMALLINT DEFAULT 0,
    war         SMALLINT DEFAULT 0,
    western     SMALLINT DEFAULT 0
);


-- 5. Bảng Ratings (tương tác cốt lõi)
CREATE TABLE ratings (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id    INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating      FLOAT,
    timestamp   BIGINT,
    UNIQUE (user_id, movie_id)
);


-- 6. Bảng Directors
CREATE TABLE directors (
    director_id SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    birth_year  INT,
    nationality VARCHAR(100)
);


-- 7. Bảng Actors
CREATE TABLE actors (
    actor_id    SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    birth_year  INT,
    nationality VARCHAR(100)
);


-- 8. Bảng movie_directors (quan hệ N-N: phim ↔ đạo diễn)
CREATE TABLE movie_directors (
    movie_id    INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    director_id INT REFERENCES directors(director_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, director_id)
);


-- 9. Bảng movie_actors (quan hệ N-N: phim ↔ diễn viên)
CREATE TABLE movie_actors (
    movie_id        INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    actor_id        INT REFERENCES actors(actor_id) ON DELETE CASCADE,
    character_name  VARCHAR(255),
    billing_order   INT DEFAULT 99,
    PRIMARY KEY (movie_id, actor_id)
);


-- 10. Bảng movie_videos (lưu trữ video theo tập)
CREATE TABLE movie_videos (
    id              SERIAL PRIMARY KEY,
    movie_id        INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    episode_no      INT,                               -- NULL = phim lẻ
    season_no       INT DEFAULT 1,
    episode_title   VARCHAR(500),
    video_url       TEXT,
    duration_mins   INT,
    video_quality   VARCHAR(20),
    file_size_mb    FLOAT,
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (movie_id, season_no, episode_no)
);


-- 11. Bảng watch_history (tiến độ xem)
CREATE TABLE watch_history (
    id                  SERIAL PRIMARY KEY,
    user_id             INT REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id            INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    episode_no          INT,
    season_no           INT DEFAULT 1,
    last_position_secs  INT DEFAULT 0,
    watch_percent       FLOAT DEFAULT 0,
    is_completed        BOOLEAN DEFAULT FALSE,
    watched_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, movie_id, season_no, COALESCE(episode_no, 0))
);


-- 12. Indexes tối ưu hiệu năng
CREATE INDEX idx_ratings_user_id   ON ratings(user_id);
CREATE INDEX idx_ratings_movie_id  ON ratings(movie_id);
CREATE INDEX idx_movies_title      ON movies USING gin(to_tsvector('english', title));
CREATE INDEX idx_watch_history_user ON watch_history(user_id);
CREATE INDEX idx_movie_videos_movie ON movie_videos(movie_id);
