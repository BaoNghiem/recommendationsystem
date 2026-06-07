import sys
from pathlib import Path
import random

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db_config import DatabaseConnector

DIRECTORS = [
    ("Christopher Nolan", 1970, "Anh"),
    ("Steven Spielberg", 1946, "Mỹ"),
    ("James Cameron", 1954, "Canada"),
    ("Quentin Tarantino", 1963, "Mỹ"),
    ("Martin Scorsese", 1942, "Mỹ"),
    ("Denis Villeneuve", 1967, "Canada"),
    ("Bong Joon-ho", 1969, "Hàn Quốc"),
    ("Wes Anderson", 1969, "Mỹ"),
    ("David Fincher", 1962, "Mỹ"),
    ("Ridley Scott", 1937, "Anh")
]

ACTORS = [
    ("Leonardo DiCaprio", 1974, "Mỹ"),
    ("Brad Pitt", 1963, "Mỹ"),
    ("Tom Hanks", 1956, "Mỹ"),
    ("Christian Bale", 1974, "Anh"),
    ("Morgan Freeman", 1937, "Mỹ"),
    ("Cillian Murphy", 1976, "Ireland"),
    ("Matthew McConaughey", 1969, "Mỹ"),
    ("Anne Hathaway", 1982, "Mỹ"),
    ("Scarlett Johansson", 1984, "Mỹ"),
    ("Natalie Portman", 1981, "Mỹ"),
    ("Song Kang-ho", 1967, "Hàn Quốc"),
    ("Robert De Niro", 1943, "Mỹ"),
    ("Al Pacino", 1940, "Mỹ"),
    ("Keanu Reeves", 1964, "Canada"),
    ("Ryan Gosling", 1980, "Canada")
]

CHARACTERS = ["The Hero", "The Villain", "The Sidekick", "The Mentor", "The Detective", "The Outlaw", "The Survivor"]

def seed_cast():
    conn = DatabaseConnector.get_connection()
    if not conn:
        print("Lỗi: Không thể kết nối CSDL.")
        return
    cur = conn.cursor()

    try:
        # Insert Directors
        print("Đang thêm Đạo diễn...")
        d_ids = []
        for name, year, nat in DIRECTORS:
            cur.execute(
                "INSERT INTO directors (name, birth_year, nationality) VALUES (%s, %s, %s) RETURNING director_id",
                (name, year, nat)
            )
            d_ids.append(cur.fetchone()[0])
        
        # Insert Actors
        print("Đang thêm Diễn viên...")
        a_ids = []
        for name, year, nat in ACTORS:
            cur.execute(
                "INSERT INTO actors (name, birth_year, nationality) VALUES (%s, %s, %s) RETURNING actor_id",
                (name, year, nat)
            )
            a_ids.append(cur.fetchone()[0])
            
        # Get top 10 movies by ID
        print("Đang lấy 10 phim có ID cao nhất...")
        cur.execute("SELECT movie_id, title FROM movies ORDER BY movie_id DESC LIMIT 10")
        top_movies = cur.fetchall()
        
        for m_id, title in top_movies:
            # Assign 1 random director
            d_id = random.choice(d_ids)
            cur.execute(
                "INSERT INTO movie_directors (movie_id, director_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (m_id, d_id)
            )
            
            # Assign 3 random actors
            selected_actors = random.sample(a_ids, 3)
            for idx, a_id in enumerate(selected_actors):
                char = random.choice(CHARACTERS)
                cur.execute(
                    "INSERT INTO movie_actors (movie_id, actor_id, character_name, billing_order) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (m_id, a_id, char, idx + 1)
                )
            print(f"Đã gán cast cho phim: {title} (ID: {m_id})")
            
        conn.commit()
        print("Thành công!")
        
    except Exception as e:
        conn.rollback()
        print("Lỗi:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_cast()
