import sqlite3
from pathlib import Path
from typing import Iterable, Optional


class Database:
    """Класс отвечает за соединение с SQLite и создание структуры БД."""

    def __init__(self, db_path: str = "support_tickets.db") -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS priorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sort_order INTEGER NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            assignee_id INTEGER,
            category_id INTEGER NOT NULL,
            priority_id INTEGER NOT NULL,
            status_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES users(id),
            FOREIGN KEY (assignee_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (priority_id) REFERENCES priorities(id),
            FOREIGN KEY (status_id) REFERENCES statuses(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users(id)
        );

        CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee_id);
        CREATE INDEX IF NOT EXISTS idx_comments_ticket ON comments(ticket_id);
        """
        with self.connect() as connection:
            connection.executescript(schema)

    def execute_many(self, query: str, values: Iterable[tuple]) -> None:
        with self.connect() as connection:
            connection.executemany(query, values)

    def execute(self, query: str, params: tuple = ()) -> int:
        with self.connect() as connection:
            cursor = connection.execute(query, params)
            return int(cursor.lastrowid or 0)

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(query, params).fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()
