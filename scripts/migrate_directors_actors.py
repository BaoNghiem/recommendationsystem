"""
Migration — Thêm bảng directors, actors, movie_directors, movie_actors
Chạy: python scripts/migrate_directors_actors.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db_config import DatabaseConnector

conn = DatabaseConnector.get_connection()
if not conn:
    print("ERROR: Cannot connect to DB")
    sys.exit(1)

cur = conn.cursor()

steps = [
    # ── 1. Bảng directors ──────────────────────────────────────
    ("Create directors table", """
        CREATE TABLE IF NOT EXISTS directors (
            director_id SERIAL PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            birth_year  SMALLINT,
            nationality VARCHAR(100),
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """),
    ("Index directors.name", """
        CREATE INDEX IF NOT EXISTS idx_directors_name ON directors(name)
    """),

    # ── 2. Bảng actors ─────────────────────────────────────────
    ("Create actors table", """
        CREATE TABLE IF NOT EXISTS actors (
            actor_id    SERIAL PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            birth_year  SMALLINT,
            nationality VARCHAR(100),
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """),
    ("Index actors.name", """
        CREATE INDEX IF NOT EXISTS idx_actors_name ON actors(name)
    """),

    # ── 3. Junction: movie_directors ───────────────────────────
    ("Create movie_directors table", """
        CREATE TABLE IF NOT EXISTS movie_directors (
            movie_id    INT NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
            director_id INT NOT NULL REFERENCES directors(director_id) ON DELETE CASCADE,
            PRIMARY KEY (movie_id, director_id)
        )
    """),
    ("Index movie_directors.director_id", """
        CREATE INDEX IF NOT EXISTS idx_movie_directors_did ON movie_directors(director_id)
    """),

    # ── 4. Junction: movie_actors ──────────────────────────────
    ("Create movie_actors table", """
        CREATE TABLE IF NOT EXISTS movie_actors (
            movie_id       INT NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
            actor_id       INT NOT NULL REFERENCES actors(actor_id) ON DELETE CASCADE,
            character_name VARCHAR(255),
            billing_order  SMALLINT DEFAULT 99,
            PRIMARY KEY (movie_id, actor_id)
        )
    """),
    ("Index movie_actors.actor_id", """
        CREATE INDEX IF NOT EXISTS idx_movie_actors_aid ON movie_actors(actor_id)
    """),
]

for name, sql in steps:
    try:
        cur.execute(sql)
        conn.commit()
        print(f"  OK  : {name}")
    except Exception as e:
        conn.rollback()
        print(f"  SKIP: {name} — {e}")

# Kiểm tra kết quả
cur.execute("SELECT COUNT(*) FROM directors")
d = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM actors")
a = cur.fetchone()[0]
print(f"\n=== MIGRATION DONE ===")
print(f"  directors : {d} records")
print(f"  actors    : {a} records")

cur.close()
conn.close()
