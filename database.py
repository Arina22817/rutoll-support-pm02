import sqlite3
from pathlib import Path
from typing import Iterable, Optional


class Database:
    """Соединение с SQLite, создание структуры и миграции учебной БД."""

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

        CREATE TABLE IF NOT EXISTS lanes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            assignee_id INTEGER,
            author_id INTEGER,
            category_id INTEGER NOT NULL,
            priority_id INTEGER NOT NULL,
            status_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            pvp TEXT NOT NULL DEFAULT '',
            lane_id INTEGER,
            tag_id INTEGER,
            component_id INTEGER,
            issue_type TEXT NOT NULL DEFAULT 'Инцидент',
            affected_version TEXT NOT NULL DEFAULT 'Не заполнено',
            environment TEXT NOT NULL DEFAULT '',
            resolution TEXT NOT NULL DEFAULT 'Нет решения',
            fix_version TEXT NOT NULL DEFAULT 'Не заполнено',
            organization TEXT NOT NULL DEFAULT '',
            group_name TEXT NOT NULL DEFAULT '',
            request_type TEXT NOT NULL DEFAULT 'Сообщить об инциденте',
            channel TEXT NOT NULL DEFAULT 'Портал',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES users(id),
            FOREIGN KEY (assignee_id) REFERENCES users(id),
            FOREIGN KEY (author_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (priority_id) REFERENCES priorities(id),
            FOREIGN KEY (status_id) REFERENCES statuses(id),
            FOREIGN KEY (lane_id) REFERENCES lanes(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id),
            FOREIGN KEY (component_id) REFERENCES components(id)
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
        """
        with self.connect() as connection:
            connection.executescript(schema)
            self._migrate_ticket_columns(connection)
            connection.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_component ON tickets(component_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_pvp ON tickets(pvp);
                CREATE INDEX IF NOT EXISTS idx_comments_ticket ON comments(ticket_id);
                """
            )

    @staticmethod
    def _migrate_ticket_columns(connection: sqlite3.Connection) -> None:
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(tickets)")}
        migrations = {
            "pvp": "ALTER TABLE tickets ADD COLUMN pvp TEXT NOT NULL DEFAULT ''",
            "lane_id": "ALTER TABLE tickets ADD COLUMN lane_id INTEGER REFERENCES lanes(id)",
            "tag_id": "ALTER TABLE tickets ADD COLUMN tag_id INTEGER REFERENCES tags(id)",
            "component_id": "ALTER TABLE tickets ADD COLUMN component_id INTEGER REFERENCES components(id)",
            "author_id": "ALTER TABLE tickets ADD COLUMN author_id INTEGER REFERENCES users(id)",
            "issue_type": "ALTER TABLE tickets ADD COLUMN issue_type TEXT NOT NULL DEFAULT 'Инцидент'",
            "affected_version": "ALTER TABLE tickets ADD COLUMN affected_version TEXT NOT NULL DEFAULT 'Не заполнено'",
            "environment": "ALTER TABLE tickets ADD COLUMN environment TEXT NOT NULL DEFAULT ''",
            "resolution": "ALTER TABLE tickets ADD COLUMN resolution TEXT NOT NULL DEFAULT 'Нет решения'",
            "fix_version": "ALTER TABLE tickets ADD COLUMN fix_version TEXT NOT NULL DEFAULT 'Не заполнено'",
            "organization": "ALTER TABLE tickets ADD COLUMN organization TEXT NOT NULL DEFAULT ''",
            "group_name": "ALTER TABLE tickets ADD COLUMN group_name TEXT NOT NULL DEFAULT ''",
            "request_type": "ALTER TABLE tickets ADD COLUMN request_type TEXT NOT NULL DEFAULT 'Сообщить об инциденте'",
            "channel": "ALTER TABLE tickets ADD COLUMN channel TEXT NOT NULL DEFAULT 'Портал'",
        }
        for column, statement in migrations.items():
            if column not in existing:
                connection.execute(statement)

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
