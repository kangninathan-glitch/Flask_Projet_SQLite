import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")
SCHEMA_PATH = Path("schema.sql")

def main():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError("schema.sql introuvable")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # Seed: 1 admin + 1 user (pour tester)
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        ("admin", "adminpass", "admin")
    )
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        ("user", "12345", "user")
    )

    # Seed: 2 livres + stock
    cursor.execute("INSERT INTO books (isbn, title, author) VALUES (?, ?, ?)", ("978-2-123", "Le Petit Prince", "Antoine de Saint-Exupéry"))
    book1_id = cursor.lastrowid
    cursor.execute("INSERT INTO book_stock (book_id, total, available) VALUES (?, ?, ?)", (book1_id, 3, 3))

    cursor.execute("INSERT INTO books (isbn, title, author) VALUES (?, ?, ?)", ("978-9-999", "1984", "George Orwell"))
    book2_id = cursor.lastrowid
    cursor.execute("INSERT INTO book_stock (book_id, total, available) VALUES (?, ?, ?)", (book2_id, 2, 2))

    conn.commit()
    conn.close()
    print("DB créée + données initiales OK")

if __name__ == "__main__":
    main()
