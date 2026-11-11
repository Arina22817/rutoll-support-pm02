from datetime import datetime
from typing import Optional

from database import Database
from models import Ticket


class TicketRepository:
    """Слой доступа к данным обращений."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create_ticket(self, ticket: Ticket) -> int:
        return self.database.execute(
            """
            INSERT INTO tickets (
                client_id, assignee_id, category_id, priority_id, status_id,
                subject, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.client_id,
                ticket.assignee_id,
                ticket.category_id,
                ticket.priority_id,
                ticket.status_id,
                ticket.subject,
                ticket.description,
                ticket.created_at,
                ticket.updated_at,
            ),
        )

    def list_tickets(self, search: str = "", status_id: Optional[int] = None) -> list:
        query = """
        SELECT
            t.id,
            t.subject,
            t.description,
            c.name AS category,
            p.name AS priority,
            s.name AS status,
            u.full_name AS client,
            COALESCE(a.full_name, 'Не назначен') AS assignee,
            t.created_at
        FROM tickets t
        JOIN categories c ON c.id = t.category_id
        JOIN priorities p ON p.id = t.priority_id
        JOIN statuses s ON s.id = t.status_id
        JOIN users u ON u.id = t.client_id
        LEFT JOIN users a ON a.id = t.assignee_id
        WHERE 1 = 1
        """
        params: list = []
        if status_id is not None:
            query += " AND t.status_id = ?"
            params.append(status_id)
        query += " ORDER BY p.sort_order ASC, t.created_at DESC"
        rows = self.database.fetch_all(query, tuple(params))
        if search.strip():
            needle = search.strip().casefold()
            rows = [
                row for row in rows
                if needle in row["subject"].casefold() or needle in row["description"].casefold()
            ]
        return rows

    def get_status_name(self, status_id: int) -> str:
        row = self.database.fetch_one("SELECT name FROM statuses WHERE id = ?", (status_id,))
        if row is None:
            raise ValueError("Неизвестный статус обращения")
        return row["name"]

    def update_status(self, ticket_id: int, status_id: int) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.database.execute(
            "UPDATE tickets SET status_id = ?, updated_at = ? WHERE id = ?",
            (status_id, now, ticket_id),
        )

    def assign(self, ticket_id: int, assignee_id: int) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.database.execute(
            "UPDATE tickets SET assignee_id = ?, updated_at = ? WHERE id = ?",
            (assignee_id, now, ticket_id),
        )


    def list_comments(self, ticket_id: int) -> list:
        return self.database.fetch_all(
            """
            SELECT c.id, c.text, c.created_at, u.full_name AS author
            FROM comments c
            JOIN users u ON u.id = c.author_id
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (ticket_id,),
        )

    def add_comment(self, ticket_id: int, author_id: int, text: str) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.database.execute(
            "INSERT INTO comments (ticket_id, author_id, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author_id, text, now),
        )
