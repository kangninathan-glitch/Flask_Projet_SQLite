DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS book_stock;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
);

CREATE TABLE books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  isbn TEXT,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- stock par livre (nb total et nb dispo)
CREATE TABLE book_stock (
  book_id INTEGER PRIMARY KEY,
  total INTEGER NOT NULL DEFAULT 1 CHECK(total >= 0),
  available INTEGER NOT NULL DEFAULT 1 CHECK(available >= 0),
  FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE TABLE loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  loaned_at TEXT NOT NULL DEFAULT (datetime('now')),
  returned_at TEXT,
  FOREIGN KEY(book_id) REFERENCES books(id),
  FOREIGN KEY(user_id) REFERENCES users(id)
);
