-- Script khoi tao cau truc Database cho Movie Recommender System
-- Design by Senior AI Engineer

-- 1. Xoa cac bang cu neu ton tai
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS movies;

-- 2. Bang Movies: Luu tru thong tin phim va dac trung noi dung
CREATE TABLE movies (
    movie_id INT PRIMARY KEY,
    title VARCHAR(500),
    genres_orig TEXT,
    -- Danh sach cac the loai phim chinh de phuc vu Filtering
    action SMALLINT DEFAULT 0,
    adventure SMALLINT DEFAULT 0,
    animation SMALLINT DEFAULT 0,
    childrens SMALLINT DEFAULT 0,
    comedy SMALLINT DEFAULT 0,
    crime SMALLINT DEFAULT 0,
    documentary SMALLINT DEFAULT 0,
    drama SMALLINT DEFAULT 0,
    fantasy SMALLINT DEFAULT 0,
    film_noir SMALLINT DEFAULT 0,
    horror SMALLINT DEFAULT 0,
    musical SMALLINT DEFAULT 0,
    mystery SMALLINT DEFAULT 0,
    romance SMALLINT DEFAULT 0,
    sci_fi SMALLINT DEFAULT 0,
    thriller SMALLINT DEFAULT 0,
    war SMALLINT DEFAULT 0,
    western SMALLINT DEFAULT 0
);

-- 3. Bang Users: Luu tru thong tin nhan khau hoc
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    gender CHAR(1),
    age INT,
    occupation INT
);

-- 4. Bang Ratings: Luu tru tuong tac (Trai tim cua he thong)
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    movie_id INT REFERENCES movies(movie_id) ON DELETE CASCADE,
    rating FLOAT,
    timestamp BIGINT
);

-- 5. Toi uu hoa hieu nang: Danh Index
-- Index giup viec lay danh sach phim mot user da xem cuc nhanh (phuc vu Recommender)
CREATE INDEX idx_ratings_user_id ON ratings(user_id);
CREATE INDEX idx_ratings_movie_id ON ratings(movie_id);
