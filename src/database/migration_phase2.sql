-- ============================================================
-- MIGRATION PHASE 2: Movie Metadata & Genre Table Separation
-- Chạy: psql -U postgres -d movie_db -f migration_phase2.sql
-- Mục đích:
--   1. Tạo bảng movie_genres (tách 18 cột binary phục vụ AI/Filter)
--   2. Thêm metadata: release_year, country, total_episodes, description
--   3. Parse release_year từ title (vd: "Toy Story (1995)")
--   4. Đảm bảo backward-compatible: AI training không bị ảnh hưởng
-- ============================================================

-- BƯỚC 1: Tạo bảng movie_genres (18 cột binary cho Content-Based + Filter)
CREATE TABLE IF NOT EXISTS movie_genres (
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

-- BƯỚC 2: Populate movie_genres từ dữ liệu hiện có trong movies
-- (Chỉ thực hiện nếu bảng movies còn có các cột binary)
INSERT INTO movie_genres (
    movie_id, action, adventure, animation, childrens, comedy, crime,
    documentary, drama, fantasy, film_noir, horror, musical, mystery,
    romance, sci_fi, thriller, war, western
)
SELECT
    movie_id, action, adventure, animation, childrens, comedy, crime,
    documentary, drama, fantasy, film_noir, horror, musical, mystery,
    romance, sci_fi, thriller, war, western
FROM movies
ON CONFLICT (movie_id) DO NOTHING;

-- BƯỚC 3: Thêm các cột metadata mới vào bảng movies
ALTER TABLE movies ADD COLUMN IF NOT EXISTS release_year  INT;
ALTER TABLE movies ADD COLUMN IF NOT EXISTS country       VARCHAR(150);
ALTER TABLE movies ADD COLUMN IF NOT EXISTS total_episodes INT;   -- NULL = phim lẻ (feature film)
ALTER TABLE movies ADD COLUMN IF NOT EXISTS description   TEXT;

-- BƯỚC 4: Parse release_year từ title bằng regex PostgreSQL
-- MovieLens title format: "Toy Story (1995)" → extract 1995
UPDATE movies
SET release_year = CAST(
    SUBSTRING(title FROM '\((\d{4})\)\s*$') AS INT
)
WHERE release_year IS NULL
  AND title ~ '\(\d{4}\)\s*$';

-- BƯỚC 5: Xóa các cột genre binary ra khỏi movies (đã chuyển sang movie_genres)
ALTER TABLE movies DROP COLUMN IF EXISTS action;
ALTER TABLE movies DROP COLUMN IF EXISTS adventure;
ALTER TABLE movies DROP COLUMN IF EXISTS animation;
ALTER TABLE movies DROP COLUMN IF EXISTS childrens;
ALTER TABLE movies DROP COLUMN IF EXISTS comedy;
ALTER TABLE movies DROP COLUMN IF EXISTS crime;
ALTER TABLE movies DROP COLUMN IF EXISTS documentary;
ALTER TABLE movies DROP COLUMN IF EXISTS drama;
ALTER TABLE movies DROP COLUMN IF EXISTS fantasy;
ALTER TABLE movies DROP COLUMN IF EXISTS film_noir;
ALTER TABLE movies DROP COLUMN IF EXISTS horror;
ALTER TABLE movies DROP COLUMN IF EXISTS musical;
ALTER TABLE movies DROP COLUMN IF EXISTS mystery;
ALTER TABLE movies DROP COLUMN IF EXISTS romance;
ALTER TABLE movies DROP COLUMN IF EXISTS sci_fi;
ALTER TABLE movies DROP COLUMN IF EXISTS thriller;
ALTER TABLE movies DROP COLUMN IF EXISTS war;
ALTER TABLE movies DROP COLUMN IF EXISTS western;

-- BƯỚC 6: Tạo index tối ưu cho movie_genres (phục vụ filter by-genre nhanh)
CREATE INDEX IF NOT EXISTS idx_mg_action      ON movie_genres(action)      WHERE action = 1;
CREATE INDEX IF NOT EXISTS idx_mg_adventure   ON movie_genres(adventure)   WHERE adventure = 1;
CREATE INDEX IF NOT EXISTS idx_mg_animation   ON movie_genres(animation)   WHERE animation = 1;
CREATE INDEX IF NOT EXISTS idx_mg_comedy      ON movie_genres(comedy)      WHERE comedy = 1;
CREATE INDEX IF NOT EXISTS idx_mg_drama       ON movie_genres(drama)       WHERE drama = 1;
CREATE INDEX IF NOT EXISTS idx_mg_horror      ON movie_genres(horror)      WHERE horror = 1;
CREATE INDEX IF NOT EXISTS idx_mg_romance     ON movie_genres(romance)     WHERE romance = 1;
CREATE INDEX IF NOT EXISTS idx_mg_sci_fi      ON movie_genres(sci_fi)      WHERE sci_fi = 1;
CREATE INDEX IF NOT EXISTS idx_mg_thriller    ON movie_genres(thriller)    WHERE thriller = 1;
CREATE INDEX IF NOT EXISTS idx_movies_year    ON movies(release_year);
CREATE INDEX IF NOT EXISTS idx_movies_country ON movies(country);

-- BƯỚC 7: Kiểm tra kết quả
SELECT
    (SELECT COUNT(*) FROM movies)                 AS total_movies,
    (SELECT COUNT(*) FROM movie_genres)           AS genres_mapped,
    (SELECT COUNT(*) FROM movies WHERE release_year IS NOT NULL) AS has_year,
    (SELECT COUNT(*) FROM movies WHERE description IS NOT NULL)  AS has_description;
